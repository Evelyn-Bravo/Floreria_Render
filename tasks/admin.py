from django.contrib import admin
from .models import Producto, Cliente, Cart, Pedido, PedidoItem
 

#ponerlos aqui es para que se vean en el admin
# Registra el modelo Producto en el admin

admin.site.site_header = "Panel de Administración - Florería"
admin.site.site_title = "Florería Admin"
admin.site.index_title = "Bienvenido al Dashboard de la Florería"

@admin.register(Producto)
class ProductoModelAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'precio', 'stock')

@admin.register(Cliente)
class ClienteModelAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'correo', 'telefono', 'direccion')

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ('id','cliente', 'producto', 'cantidad')

# Clase Inline para mostrar los ítems de pedido dentro del pedido
class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0

# Registrando el modelo Pedido con una clase personalizada
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'metodo_pago', 'estado', 'total')
    list_filter = ('estado', 'fecha', 'metodo_pago')
    search_fields = ('cliente__nombre', 'id')
    date_hierarchy = 'fecha'
    inlines = [PedidoItemInline]