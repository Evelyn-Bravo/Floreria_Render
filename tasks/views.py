from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from .models import Producto, Cliente, Cart, Pedido,PedidoItem  # Importamos nuestros modelos
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from django.http import JsonResponse

# Create your views here.


def home(request):
    return render(request, 'home.html')

def signup(request):

    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                # registrar usuario
                user = User.objects.create_user(username=request.POST['username'],
                                                password=request.POST['password1'])
                user.save() # registrar el usuario en la base de datos
                login(request, user) # iniciar sesion automaticamente
                return redirect('home')
            except Exception:
                return render(request, 'signup.html', {
                    'form': UserCreationForm,
                    "error": 'El usuario ya existe'
                })
        return render(request, 'signup.html', {
            'form': UserCreationForm,
            "error": 'Las contraseñas no coinciden'
        })

        # print(request.POST) #mostrar en consola los datos que el usuario ingreso

def carrito(request):
    # Verificar si el usuario está autenticado
    if not request.user.is_authenticated:
        # Si se está intentando agregar un producto, redirige a signin con next=carrito
        producto_id = request.GET.get('producto_id')
        if producto_id:
            return redirect(f'/signin/?next=/carrito/?producto_id={producto_id}')
        
        # Si solo se está intentando ver el carrito, muestra un mensaje
        return render(request, 'carrito.html', {
            'carrito': [],
            'mensaje': 'Por favor, inicia sesión para ver tu carrito'
        })

    user = request.user
    
    # Procesar la adición al carrito si hay un producto_id en la solicitud
    producto_id = request.GET.get('producto_id')
    
    if producto_id:
        if not producto_id.isdigit():
            messages.error(request, 'Producto no válido.')
            return redirect('catalogo')
        try:
            # Obtener el producto
            producto_obj = Producto.objects.get(id=producto_id)
            
             # Verificar si hay stock disponible
            if producto_obj.stock <= 0:
                messages.warning(request, f'No hay stock disponible de {producto_obj.nombre}')
                return redirect('catalogo')

            # Obtener o crear cliente para el usuario actual
            cliente, created_cliente = Cliente.objects.get_or_create(
                usuario=user,
                defaults={
                    'nombre': user.username,
                    'correo': user.email if hasattr(user, 'email') and user.email else f"{user.username}@example.com",
                    'telefono': '',
                    'direccion': ''
                }
            )
            
            # Verificar si el producto ya está en el carrito
            cart_item, created = Cart.objects.get_or_create(
                cliente=cliente,
                producto=producto_obj,
                defaults={'cantidad': 1}
            )
            
            # Si el producto ya existía en el carrito, incrementar cantidad
            if not created:
                cart_item.cantidad += 1
                cart_item.save()
            
            # Redireccionar de vuelta al catálogo después de agregar el producto
            return redirect('catalogo')
            
        except Producto.DoesNotExist:
            messages.error(request, 'El producto no existe.')
            return redirect('catalogo')
        except Exception as e:
            messages.error(request, 'Ocurrió un error al agregar el producto al carrito.')
            return redirect('catalogo')
    
    # Mostrar el carrito solo si no estamos agregando productos
    try:
        cliente = Cliente.objects.get(usuario=user) # Obtener el cliente asociado al usuario
        carrito_items = Cart.objects.filter(cliente=cliente) # Obtener los productos en el carrito
        
        # Calcular totales
        total_items = sum(item.cantidad for item in carrito_items)
        total = sum(item.subtotal for item in carrito_items)
        costo_envio = Decimal('150.00')  
        total = total + costo_envio  # Incluir costo de envío
        
        context = { #context es un diccionario que contiene los datos que se van a enviar a la plantilla
            'carrito': carrito_items,
            'total_items': total_items,
            'costo_envio': costo_envio,  
            'total': total
        }
        
        return render(request, 'carrito.html', context)
    except Cliente.DoesNotExist:
        return render(request, 'carrito.html', {'carrito': []})
    except Exception as e:
        messages.error(request, 'Ocurrió un error al cargar el carrito.')
        return render(request, 'carrito.html', {'carrito': []})

def signout(request):
    logout(request)
    return redirect('home')

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user=authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html',{
            'form': AuthenticationForm,
            'error': 'El usuario o contraseña es incorrecta'
        })
        else:
            login(request, user)
            return redirect('home')
        
@login_required
def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('producto_id')
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            cart_item = Cart.objects.get(cliente=cliente, producto__id=prod_id)
            cart_item.cantidad += 1
            cart_item.save()
            
            # Recalcular totales
            carrito = Cart.objects.filter(cliente=cliente)
            total_items = sum(item.cantidad for item in carrito)
            total = sum(item.subtotal for item in carrito)

            costo_envio = Decimal('150.00')  # Costo de envío fijo 
            data = {
                'cantidad': cart_item.cantidad,
                'subtotal': Decimal(cart_item.subtotal),
                'total_items': total_items,
                'total': Decimal(total + costo_envio)
            }
            
            return JsonResponse(data)
        except (Cliente.DoesNotExist, Cart.DoesNotExist):
            return JsonResponse({'error': 'Producto no encontrado en el carrito'}, status=404)

@login_required
def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('producto_id')
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            cart_item = Cart.objects.get(cliente=cliente, producto__id=prod_id)
            
            if cart_item.cantidad > 1:
                cart_item.cantidad -= 1
                cart_item.save()
            else:
                cart_item.delete()
                
            # Recalcular totales
            carrito = Cart.objects.filter(cliente=cliente)
            total_items = sum(item.cantidad for item in carrito)
            total = sum(item.subtotal for item in carrito)
            
            costo_envio = Decimal('150.00')  # Costo de envío fijo
            data = {
                'cantidad': cart_item.cantidad if cart_item.cantidad > 0 else 0,
                'subtotal': Decimal(cart_item.subtotal) if cart_item.cantidad > 0 else 0,
                'total_items': total_items,
                'total': Decimal(total + costo_envio)
            }
            
            return JsonResponse(data)
        except (Cliente.DoesNotExist, Cart.DoesNotExist):
            return JsonResponse({'error': 'Producto no encontrado en el carrito'}, status=404)

@login_required
def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('producto_id')
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            cart_item = Cart.objects.get(cliente=cliente, producto__id=prod_id)
            cart_item.delete()
            
            # Recalcular totales
            carrito = Cart.objects.filter(cliente=cliente)
            total_items = sum(item.cantidad for item in carrito)
            total = sum(item.subtotal for item in carrito)
            
            costo_envio = Decimal('150.00')  # Costo de envío fijo
            data = {
                'total_items': total_items,
                'total': Decimal(total + costo_envio)
            }
            
            return JsonResponse(data)
        except (Cliente.DoesNotExist, Cart.DoesNotExist):
            return JsonResponse({'error': 'Producto no encontrado en el carrito'}, status=404) 

@login_required
def vaciar_carrito(request):
    if request.method != 'POST':
        return redirect('carrito')
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        Cart.objects.filter(cliente=cliente).delete()
        return redirect('carrito')
    except Exception as e:
        messages.error(request, 'Ocurrió un error al vaciar el carrito.')
        return redirect('carrito')

def catalogo(request):
    productos = Producto.objects.all()  # Obtener todos los productos
    return render(request, 'catalogo.html', {'productos': productos})

#faltan las vistas de checkout, pago exitoso y perfil
@login_required
def perfil(request):
    # Obtener o crear un objeto Cliente asociado al usuario
    cliente, created = Cliente.objects.get_or_create(
        usuario=request.user,
        defaults={
            'nombre': request.user.username,
            'correo': request.user.email if request.user.email else '',
        }
    )
    
    if request.method == 'POST':
        # Validar que el correo no venga vacío
        correo = request.POST.get('correo', '').strip()
        if not correo or '@' not in correo:
            messages.error(request, 'Por favor ingresa un correo electrónico válido.')
            return render(request, 'perfil.html', {'cliente': cliente, 'pedidos': Pedido.objects.filter(cliente=cliente).order_by('-fecha')})

        # Actualizar datos del cliente con los datos del formulario en la base de datos
        cliente.nombre = request.POST.get('nombre', '')
        cliente.apellido = request.POST.get('apellido', '')
        cliente.correo = correo
        cliente.telefono = request.POST.get('telefono', '')
        cliente.direccion = request.POST.get('direccion', '')
        cliente.ciudad = request.POST.get('ciudad', '')
        cliente.estado = request.POST.get('estado', '')
        cliente.codigo_postal = request.POST.get('codigo_postal', '')
        cliente.save()
        
        # También actualizar el email del usuario
        request.user.email = correo
        request.user.save()
        
        # Mensaje de éxito
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('home')
    
    # Obtener los pedidos del cliente
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha')
    
    context = {
        'cliente': cliente,
        'pedidos': pedidos
    }
    return render(request, 'perfil.html', context)

@login_required
def checkout(request):
    user = request.user
    
    try:
        # Obtener el cliente y su carrito
        cliente = Cliente.objects.get(usuario=user)
        carrito = Cart.objects.filter(cliente=cliente)
        
        if not carrito.exists():
            messages.warning(request, 'Tu carrito está vacío')
            return redirect('carrito')
        
        # Calcular totales
        subtotal = sum(item.subtotal for item in carrito)
        costo_envio = Decimal('150.00')
        total = subtotal + costo_envio
        
        if request.method == 'POST':
            # Verificar stock antes de procesar la compra
            for item in carrito:
                if item.cantidad > item.producto.stock:
                    messages.error(request, f'No hay suficiente stock de {item.producto.nombre}. Stock disponible: {item.producto.stock}')
                    return redirect('carrito')
            
            # Crear un nuevo pedido
            pedido = Pedido(
                cliente=cliente,
                metodo_pago=request.POST.get('metodo_pago', 'efectivo'),
                total=total,
                estado='pendiente'
            )
            pedido.save()
            
            # Guardar los ítems del pedido y actualizar stock
            for item in carrito:
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio=item.producto.precio
                )
                
                # Actualizar el stock
                producto = item.producto
                producto.stock -= item.cantidad
                producto.save()
            
            # Limpiar carrito
            carrito.delete()
            
            messages.success(request, '¡Pedido realizado con éxito! Gracias por tu compra.')
            return redirect('pago_exitoso', pedido_id=pedido.id)  # Forma correcta
        
        context = {
            'carrito': carrito,
            'subtotal': subtotal,
            'costo_envio': costo_envio,
            'total': total,
            'cliente': cliente
        }
        
        return render(request, 'checkout.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Necesitas completar tu perfil antes de realizar una compra')
        return redirect('perfil')
    except Exception:
        messages.error(request, 'Ocurrió un error inesperado al procesar tu pedido. Intenta de nuevo.')
        return redirect('carrito')

@login_required
def pago_exitoso(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id, cliente__usuario=request.user) # Verificar que el pedido pertenece al usuario
        return render(request, 'pago_exitoso.html', {'pedido': pedido})  # Mostrar detalles del pedido
    except Pedido.DoesNotExist:
        messages.error(request, 'El pedido no existe o no tienes permiso para verlo.')
        return redirect('home')