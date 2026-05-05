from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Producto, Cliente, Cart, Pedido, PedidoItem

# pruebas de autenticacion
class AutenticacionTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='evelyn', password='test1234'
        )

    # verificar que el login funciona con datos correctos
    def test_login_correcto(self):
        response = self.client.post(reverse('signin'), {
            'username': 'evelyn',
            'password': 'test1234'
        })
        self.assertEqual(response.status_code, 302)

    # verificar que el login falla con contrasena incorrecta
    def test_login_incorrecto(self):
        response = self.client.post(reverse('signin'), {
            'username': 'evelyn',
            'password': 'wrongpass'
        })
        self.assertContains(response, 'incorrecta')

    # verificar que se puede registrar un usuario nuevo
    def test_registro_usuario_nuevo(self):
        response = self.client.post(reverse('signup'), {
            'username': 'nuevo_usuario',
            'password1': 'pass5678',
            'password2': 'pass5678'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='nuevo_usuario').exists())

    # verificar que el registro falla si las contrasenas no coinciden
    def test_registro_contrasenas_no_coinciden(self):
        response = self.client.post(reverse('signup'), {
            'username': 'otro_usuario',
            'password1': 'pass5678',
            'password2': 'diferente'
        })
        self.assertContains(response, 'coinciden')


# pruebas del carrito
class CarritoTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='evelyn', password='test1234'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nombre='Evelyn',
            apellido='Bravo',
            correo='evelyn@test.com'
        )
        self.producto = Producto.objects.create(
            nombre='Ramo de Rosas',
            descripcion='Ramo con 12 rosas rojas',
            precio=Decimal('250.00'),
            stock=10,
            categoria='ramo de flores'
        )

    # si no hay sesion el carrito no debe mostrarse
    def test_carrito_sin_login_redirige(self):
        response = self.client.get(reverse('carrito'))
        self.assertContains(response, 'inicia sesión')

    # verificar que el producto se agrega al carrito correctamente
    def test_agregar_producto_al_carrito(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('carrito'), {'producto_id': self.producto.id})
        self.assertTrue(
            Cart.objects.filter(cliente=self.cliente, producto=self.producto).exists()
        )

    # el subtotal debe ser cantidad x precio
    def test_subtotal_carrito_correcto(self):
        cart_item = Cart.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=3
        )
        self.assertEqual(cart_item.subtotal, Decimal('750.00'))

    # un producto sin stock no debe poder agregarse
    def test_producto_sin_stock_no_se_agrega(self):
        self.producto.stock = 0
        self.producto.save()
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('carrito'), {'producto_id': self.producto.id})
        self.assertFalse(
            Cart.objects.filter(cliente=self.cliente, producto=self.producto).exists()
        )


# pruebas de checkout
class CheckoutTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='evelyn', password='test1234'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nombre='Evelyn',
            apellido='Bravo',
            correo='evelyn@test.com'
        )
        self.producto = Producto.objects.create(
            nombre='Arreglo Primaveral',
            descripcion='Arreglo con flores de temporada',
            precio=Decimal('400.00'),
            stock=5,
            categoria='arreglo floral'
        )
        self.cart_item = Cart.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=2
        )

    # al hacer checkout el stock debe descontarse
    def test_checkout_descuenta_stock(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('checkout'), {'metodo_pago': 'efectivo'})
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    # el carrito debe vaciarse despues del checkout
    def test_checkout_vacia_carrito(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('checkout'), {'metodo_pago': 'efectivo'})
        self.assertFalse(Cart.objects.filter(cliente=self.cliente).exists())

    # debe crearse un pedido en la base de datos
    def test_checkout_crea_pedido(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('checkout'), {'metodo_pago': 'efectivo'})
        self.assertTrue(Pedido.objects.filter(cliente=self.cliente).exists())

    # si el carrito esta vacio debe redirigir
    def test_checkout_carrito_vacio_redirige(self):
        self.client.login(username='evelyn', password='test1234')
        Cart.objects.filter(cliente=self.cliente).delete()
        response = self.client.post(reverse('checkout'), {'metodo_pago': 'efectivo'})
        self.assertRedirects(response, reverse('carrito'))