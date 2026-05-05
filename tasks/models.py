from django.db import models
from django.contrib.auth.models import User

# Create your models here.

CATEGORIA_CHOICES = (
    ('arreglo floral', 'Arreglo Floral'),
    ('ramo de flores', 'Ramo de Flores'),
    ('jarrones', 'Jarrones'),
)

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.CharField(choices=CATEGORIA_CHOICES,max_length=50)
    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    def __str__(self):
        return self.nombre

class Cart(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    @property
    def subtotal(self):
        return self.cantidad * self.producto.precio
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} ({self.cliente.nombre})"


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio