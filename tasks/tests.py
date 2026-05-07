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
        self.assertContains(response, 'Carrito de Compras Vacío')

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


# pruebas de plus_cart, minus_cart, remove_cart y vaciar_carrito
class CarritoAccionesTest(TestCase):

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
        self.cart_item = Cart.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=2
        )

    # plus_cart debe incrementar la cantidad en 1
    def test_plus_cart_incrementa_cantidad(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('plus_cart'), {'producto_id': self.producto.id})
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.cantidad, 3)

    # minus_cart debe decrementar la cantidad en 1
    def test_minus_cart_decrementa_cantidad(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('minus_cart'), {'producto_id': self.producto.id})
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.cantidad, 1)

    # minus_cart con cantidad 1 debe eliminar el item
    def test_minus_cart_elimina_cuando_cantidad_es_uno(self):
        self.cart_item.cantidad = 1
        self.cart_item.save()
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('minus_cart'), {'producto_id': self.producto.id})
        self.assertFalse(Cart.objects.filter(id=self.cart_item.id).exists())

    # remove_cart debe eliminar el item del carrito
    def test_remove_cart_elimina_item(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('remove_cart'), {'producto_id': self.producto.id})
        self.assertFalse(Cart.objects.filter(id=self.cart_item.id).exists())

    # vaciar_carrito debe eliminar todos los items del cliente
    def test_vaciar_carrito_elimina_todo(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('vaciar_carrito'))
        self.assertFalse(Cart.objects.filter(cliente=self.cliente).exists())

    # vaciar_carrito por GET no debe eliminar nada (requiere POST)
    def test_vaciar_carrito_get_no_elimina(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.get(reverse('vaciar_carrito'))
        self.assertTrue(Cart.objects.filter(cliente=self.cliente).exists())

    # producto_id no numerico debe redirigir con error
    def test_carrito_producto_id_invalido(self):
        self.client.login(username='evelyn', password='test1234')
        response = self.client.get(reverse('carrito'), {'producto_id': 'abc'})
        self.assertEqual(response.status_code, 302)


# pruebas de perfil
class PerfilTest(TestCase):

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

    # perfil sin login debe redirigir al signin
    def test_perfil_sin_login_redirige(self):
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 302)

    # actualizacion de datos correcta
    def test_perfil_actualiza_datos(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('perfil'), {
            'nombre': 'Evelyn',
            'apellido': 'Bravo',
            'correo': 'nuevo@test.com',
            'telefono': '6561234567',
            'direccion': 'Calle 1',
            'ciudad': 'Juarez',
            'estado': 'Chihuahua',
            'codigo_postal': '32000'
        })
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.correo, 'nuevo@test.com')

    # correo invalido no debe guardarse
    def test_perfil_correo_invalido_no_guarda(self):
        self.client.login(username='evelyn', password='test1234')
        self.client.post(reverse('perfil'), {
            'nombre': 'Evelyn',
            'apellido': 'Bravo',
            'correo': 'correo_sin_arroba',
            'telefono': '',
            'direccion': '',
            'ciudad': '',
            'estado': '',
            'codigo_postal': ''
        })
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.correo, 'evelyn@test.com')


# pruebas de pago_exitoso
class PagoExitosoTest(TestCase):

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
            descripcion='Flores de temporada',
            precio=Decimal('400.00'),
            stock=5,
            categoria='arreglo floral'
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            metodo_pago='efectivo',
            total=Decimal('550.00'),
            estado='pendiente'
        )

    # pago_exitoso sin login debe redirigir
    def test_pago_exitoso_sin_login_redirige(self):
        response = self.client.get(reverse('pago_exitoso', args=[self.pedido.id]))
        self.assertEqual(response.status_code, 302)

    # pago_exitoso con login debe mostrar el pedido
    def test_pago_exitoso_muestra_pedido(self):
        self.client.login(username='evelyn', password='test1234')
        response = self.client.get(reverse('pago_exitoso', args=[self.pedido.id]))
        self.assertEqual(response.status_code, 200)

    # pago_exitoso con pedido que no pertenece al usuario debe redirigir
    def test_pago_exitoso_pedido_ajeno_redirige(self):
        otro_user = User.objects.create_user(username='otro', password='test1234')
        self.client.login(username='otro', password='test1234')
        response = self.client.get(reverse('pago_exitoso', args=[self.pedido.id]))
        self.assertEqual(response.status_code, 302)


# pruebas de catalogo
class CatalogoTest(TestCase):

    def setUp(self):
        self.client = Client()
        Producto.objects.create(
            nombre='Rosa Roja',
            descripcion='Rosa fresca',
            precio=Decimal('50.00'),
            stock=5,
            categoria='ramo de flores'
        )
        Producto.objects.create(
            nombre='Arreglo de Girasoles',
            descripcion='Girasoles frescos',
            precio=Decimal('300.00'),
            stock=3,
            categoria='arreglo floral'
        )

    # el catalogo debe cargar correctamente sin login
    def test_catalogo_carga_sin_login(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)

    # el catalogo debe mostrar todos los productos
    def test_catalogo_muestra_productos(self):
        response = self.client.get(reverse('catalogo'))
        self.assertContains(response, 'Rosa Roja')
        self.assertContains(response, 'Arreglo de Girasoles')