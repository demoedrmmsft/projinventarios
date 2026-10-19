# Lote LAB - Guia de pantallas y flujos

Manual de operacion de la version actual. Para instalar, iniciar, respaldar y configurar tareas de Windows,
consulte [README.md](README.md). Las rutas de este manual se agregan a `http://127.0.0.1:8000`;
si usa otro puerto, conserve ese puerto durante todo el recorrido.

Los ejemplos numericos son ilustrativos: no cargan datos de demostracion y no sustituyen el cotejo fisico.

## 1. Roles y permisos

| Accion | Auditor | Operador | Responsable | Superusuario |
| --- | --- | --- | --- | --- |
| Consultar resumen, catalogo, existencias, movimientos y alertas | Si | Si | Si | Si |
| Exportar movimientos | Si | Si | Si | Si |
| Registrar entradas, aperturas y consumos | No | Si | Si | Si |
| Crear productos, registrar bajas y revertir salidas | No | No | Si | Si |
| Cambiar estado/cuarentena del lote | No | No | Si | Si |
| Preparar, confirmar u omitir filas del Excel | No | No | Si | Si |
| Configurar correo | No | No | Si | Si |
| Administrar usuarios y grupos | No | No | No | Si |

La tabla supone los grupos predeterminados. Los permisos individuales pueden modificar el acceso.
Los botones dependen del rol; una URL directa no evita los controles del servidor.
Una cuenta nueva sin grupo no tiene automaticamente acceso al inventario.

## 2. Mapa de pantallas

| Pantalla | Ruta | Entrada habitual |
| --- | --- | --- |
| Alta inicial | `/setup/` | Primera visita, si no existen usuarios |
| Iniciar sesion | `/accounts/login/` | Acceso sin sesion |
| Resumen | `/` | Menu Resumen o inicio de sesion |
| Catalogo | `/products/` | Menu Catalogo |
| Registrar entrada | `/stocks/new/` | Resumen, Existencias o icono de entrada del producto |
| Existencias | `/stocks/` | Menu Existencias |
| Detalle de partida/envase | `/stocks/<id>/` | Nombre del producto o icono Ver detalle |
| Movimientos | `/movements/` | Menu Movimientos |
| Revertir salida | `/movements/<id>/reverse/` | Icono Revertir salida de un consumo o baja |
| Exportar CSV | `/movements/export/` | Boton Exportar CSV; inicia una descarga |
| Revision de Excel | `/imports/` | Menu Revision de Excel |
| Detalle del libro | `/imports/<id>/` | Nombre del archivo o boton Revisar |
| Confirmar saldo inicial | `/imports/rows/<id>/` | Boton Revisar de una fila pendiente |
| Alertas | `/alerts/` | Menu Alertas |
| Configurar correo | `/settings/mail/` | Boton Configurar correo en Alertas |
| Administracion | `/admin/` | Enlace Administracion de usuarios del superusuario |
| Cerrar sesion | `/accounts/logout/` | Boton Cerrar sesion del menu; no abrir como enlace directo |

`<id>` representa el identificador real del registro. No escriba literalmente los signos `<` y `>`.
En movil, abra el menu superior. Las tablas anchas tienen desplazamiento horizontal propio.
Las listas paginadas muestran 30 registros por pagina y controles para avanzar o retroceder.

## 3. Alta inicial del administrador

Condicion: la base no contiene ningun usuario. No existe una cuenta o contrasena predeterminada.

1. Abra la aplicacion. Sera dirigido a Administrador del almacen.
2. Escriba un nombre de usuario y una contrasena que cumpla las reglas mostradas.
3. Repita la contrasena en Confirmacion de contrasena.
4. Presione Crear administrador.

Resultado: se crea un superusuario, se preparan los grupos y se abre Resumen con la sesion iniciada.
Si hay errores, corrija los campos indicados; una contrasena demasiado similar al usuario se rechaza.
Una vez creado el primer usuario, `/setup/` deja de permitir altas. Los demas usuarios se crean desde Administracion.
Este paso no importa Excel, no crea productos y no autoriza correo.

## 4. Iniciar y cerrar sesion

1. Abra la aplicacion e introduzca Nombre de usuario y Contrasena.
2. Presione Entrar.
3. Acceda a Resumen o a la pantalla protegida que habia solicitado.
4. Al terminar, use Cerrar sesion, junto al nombre del usuario en el menu.

Resultado al salir: la aplicacion regresa a Iniciar sesion. Cerrar sesion no detiene el servidor ni borra datos.
Una cuenta sin permisos puede autenticarse y aun asi recibir acceso denegado; el superusuario debe revisar su grupo.
La aplicacion no tiene recuperacion de contrasena por correo; vea los procedimientos de soporte en [README.md](README.md).

## 5. Resumen del inventario

Disponible para los cuatro roles con permisos de consulta.

1. Abra Resumen en el menu.
2. Revise Productos en catalogo, Partidas disponibles, Proximas a vencer y Partidas vencidas.
3. Presione una cifra para abrir el catalogo o la lista de existencias con el filtro correspondiente.
4. Revise Atencion por caducidad, Ultimos movimientos y Existencia minima.
5. Si tiene permiso, use Registrar entrada o abra las filas pendientes de Revision de Excel.

Partidas disponibles cuenta registros con saldo util, no cajas ni volumen total. Dos frascos del mismo lote
pueden contar como dos partidas. Proximas a vencer considera hasta 90 dias y solo material util.
La existencia minima compara el saldo util de cada producto con su minimo, en su propia unidad base.
No se suman piezas, mL y gramos entre productos. Una base nueva muestra contadores en cero.

## 6. Catalogo: consultar y crear productos

Consulta: todos los roles. Alta: Responsable o Superusuario.

1. Abra Catalogo y busque por nombre o categoria, si es necesario.
2. Para crear una ficha, presione Nuevo producto; se abrira el formulario dentro de la misma pagina.
3. Complete Nombre, Categoria y Unidad base: piezas, mililitros o gramos.
4. Indique Presentacion, por ejemplo Caja o Frasco, y Contenido por presentacion en la unidad base.
5. Indique Existencia minima; cero no genera avisos de minimo.
6. Mantenga Requiere caducidad si aplica al producto. Desmarquelo solo cuando este justificado.
7. Capture Dias utiles tras apertura, si el fabricante define ese plazo, y Condiciones de almacenamiento.
8. Presione Guardar producto.

Resultado: la ficha aparece en el catalogo y se registra su alta en auditoria. Todavia no hay existencias.
El nombre no puede repetirse exactamente. Para piezas, contenido y minimo deben ser enteros.
Contenido debe ser positivo; los dias tras apertura, si se capturan, deben ser al menos uno.

Ejemplos de fichas: Caja de gasas, unidad piezas, contenido 100; Reactivo liquido, unidad mL, frasco de 500.
Una JERINGA 10 ML normalmente se cuenta en piezas: su capacidad no es un saldo de liquido.
Esta version permite crear y consultar fichas, pero no ofrece una pantalla para editarlas o eliminarlas.
Verifique unidad y equivalencia antes de guardar; no intente corregirlas editando SQLite.

## 7. Registrar una entrada manual

Disponible para Operador, Responsable y Superusuario. Requiere una ficha de producto existente.

1. Presione Registrar entrada desde Resumen o Existencias, o el icono de entrada de una fila del Catalogo.
2. Seleccione Producto y coteje la unidad base de su ficha.
3. Capture Lote verificado, Caducidad verificada y Ubicacion.
4. Indique Numero de cajas / envases y Contenido por caja / envase en la unidad base.
5. Revise el total mostrado y escriba Motivo / referencia de recepcion.
6. Marque Datos y saldo fisico verificados.
7. Presione Guardar entrada.

Resultado: se crean las existencias, sus movimientos de Entrada y se abre el detalle de la primera partida/envase.
Una entrada manual adicional al mismo producto/lote es posible si coincide su caducidad y ubicacion;
es una recepcion adicional, no una sustitucion del saldo anterior.

| Ejemplo | Captura | Resultado |
| --- | --- | --- |
| Cinco cajas con cien piezas cada una | Cajas 5, contenido 100, unidad piezas | Una partida de 500 piezas |
| Dos frascos de quinientos mL | Envases 2, contenido 500, unidad mL | Dos envases separados de 500 mL |
| Un frasco parcial de 487.5 mL verificados | Envases 1, contenido 487.5, unidad mL | Un registro de 487.5 mL |

En piezas y gramos, las presentaciones se agregan en una partida por entrada. En mL se crea un registro por envase.
El contenido se puede ajustar para reflejar el saldo fisico verificado; no deduzca sobrantes a partir de formulas antiguas.
Para un envase ya abierto, registre despues su fecha real de apertura antes del consumo cuando corresponda.

Validaciones: entre 1 y 1000 cajas/envases, cantidades positivas de hasta tres decimales y piezas enteras.
Caducidad es obligatoria si la ficha lo requiere. `S/L` y `S/F` no son lotes validos: coteje etiqueta o documente
un identificador interno para material realmente sin lote. No se fusiona un producto/lote con otra fecha o ubicacion.
Una recepcion vencida puede documentarse, pero no queda habilitada para consumo.

## 8. Existencias: buscar y seleccionar material

1. Abra Existencias.
2. Busque por producto, lote o ubicacion.
3. Seleccione Todas con saldo, Disponibles, Por vencer, Vencidas o No disponibles y presione Filtrar.
4. Revise saldo, unidad, caducidad efectiva, apertura y estado.
5. Abra el nombre del producto o el icono Ver detalle de la partida que va a operar.

La lista solo muestra partidas con saldo positivo. Las agotadas conservan su historial en Movimientos
y siguen accesibles desde los enlaces de sus movimientos.
El orden FEFO prioriza material util con menor caducidad efectiva; no selecciona ni descuenta automaticamente.
Por vencer incluye hasta 90 dias. No disponibles incluye material vencido o bloqueado por estado/fecha.
No consuma un envase distinto del que selecciono en pantalla.

## 9. Detalle de partida/envase

El encabezado identifica producto, lote y numero de partida/envase. Revise Saldo disponible, Caducidad efectiva,
Caducidad fabricante, Apertura, Estado del lote, Recepcion, Ubicacion y Almacenamiento antes de operar.
Los formularios dependen del rol y del estado de la partida. La trazabilidad inferior muestra sus movimientos.

### 9.1 Registrar apertura

1. Abra el detalle de un envase util que todavia no tenga apertura.
2. En Apertura de envase indique Fecha de apertura.
3. Presione Registrar apertura.

Resultado: queda un movimiento Apertura de cantidad cero y el saldo no cambia.
La fecha no puede ser futura y no se registra una segunda apertura sobre el mismo envase.
Si existe plazo tras apertura, la caducidad efectiva pasa a ser la menor entre la del fabricante
y la fecha de apertura mas ese plazo. El dia de caducidad se considera valido hasta finalizar en horario CDMX.
Si la apertura real ya produjo vencimiento, el consumo quedara bloqueado.
La version actual no tiene formulario para corregir una apertura registrada; verifique la fecha antes de confirmar.

### 9.2 Registrar consumo completo o parcial

1. Abra el detalle y compruebe que el material este disponible.
2. Si el producto tiene dias utiles tras apertura, registre primero su apertura.
3. En Registrar salida, capture Cantidad en la unidad base, no numero de cajas.
4. Escriba Destino / motivo y presione Registrar consumo.

Resultado: se descuenta el saldo y se registra responsable, fecha, motivo y saldo posterior.
Ejemplo parcial: 500 mL menos 12.5 mL deja 487.5 mL. Para consumir todo, capture el saldo completo disponible.
El servidor rechaza exceso de saldo, cantidades no positivas, fracciones de pieza, material vencido, bloqueado,
agotado o sin la caducidad requerida. No basta con que la pantalla estuviera abierta antes de vencer.
Un saldo en cero desaparece de Existencias, pero no pierde su historial.

### 9.3 Registrar baja

Disponible solo para Responsable o Superusuario.

1. Abra la partida que debe retirarse.
2. Capture la cantidad a retirar en Registrar salida.
3. Escriba el motivo: vencimiento, dano, derrame u otra causa documentada.
4. Presione Registrar baja, no Registrar consumo.

Resultado: disminuye el saldo y queda un movimiento Baja. Se permite retirar material vencido o bloqueado,
pero nunca mas cantidad de la que existe. La baja en el sistema no sustituye el procedimiento fisico
de disposicion de residuos del laboratorio. Para retirar todo, capture el saldo completo.

### 9.4 Cuarentena y estado del lote

Disponible solo para Responsable o Superusuario.

1. Despliegue Estado y cuarentena del lote en el detalle.
2. Seleccione Aceptado, Pendiente de revision o Cuarentena.
3. Escriba Motivo del cambio y presione Actualizar estado.

Resultado: cambia el estado del lote completo, incluidos todos sus envases, y se registra auditoria.
Pendiente de revision y Cuarentena bloquean el consumo, sin descontar existencias.
Para liberar, un responsable selecciona Aceptado con motivo; esto no elimina un vencimiento ni reemplaza
la caducidad, la apertura o el saldo. Una partida vencida sigue sin ser util aunque su lote este aceptado.

## 10. Movimientos, exportacion y reversion

### 10.1 Consultar trazabilidad

1. Abra Movimientos o la trazabilidad de una partida.
2. En Movimientos busque por producto, lote o responsable y presione Buscar.
3. Revise fecha CDMX, usuario, partida, tipo, cantidad, saldo posterior y motivo.
4. Use el enlace del producto para volver a la partida, incluso si ya esta agotada.

Entrada y Reversion suman saldo; Consumo y Baja lo restan; Apertura registra cero.
La seccion Auditoria del catalogo y lotes muestra los 20 eventos mas recientes, como altas,
cambios de estado, omisiones de Excel y configuracion de correo. No es una pantalla de edicion.

### 10.2 Exportar CSV

1. En Movimientos, presione Exportar CSV.
2. Abra la descarga `movimientos.csv` con Excel u otra herramienta compatible con UTF-8.
3. Compruebe la unidad de cada registro antes de sumar cantidades.

La exportacion incluye todos los movimientos, no solo la pagina ni el filtro de busqueda de la pantalla.
No incluye la auditoria del catalogo como filas de movimiento. Algunos textos pueden llevar un apostrofo
de proteccion para evitar que una hoja de calculo los ejecute como formulas.

### 10.3 Revertir una salida equivocada

Disponible solo para Responsable o Superusuario.

1. Localice el Consumo o la Baja incorrectos.
2. Presione el icono Revertir salida de esa fila.
3. En Revertir salida, documente Motivo de la reversion.
4. Presione Confirmar reversion.

Resultado: se restaura la cantidad de la salida y se vuelve al detalle de la partida.
Se conserva el movimiento original y se agrega una reversion vinculada; una salida solo se revierte una vez.
No se revierten entradas ni aperturas por esta pantalla. El saldo no puede superar lo recibido inicialmente.
Si la cantidad correcta era otra, revierta la salida completa y capture una nueva salida correcta.
Revertir devuelve saldo, pero no cambia la caducidad ni libera una cuarentena.

## 11. Revision de Excel

Disponible para Responsable y Superusuario. Este flujo carga saldos iniciales conciliados, no historial antiguo.

### 11.1 Preparar un libro

1. Abra Revision de Excel.
2. Seleccione el libro `.xlsx`, de hasta 5 MB.
3. Presione Preparar revision.

Resultado: se abre el detalle del libro sin aumentar existencias ni crear productos.
Se reconocen las hojas `INVENTARIO ALMACEN` e `INVENTARIO REACTIVOS` con los encabezados del formato original.
Se procesa el bloque izquierdo: los nombres/lotes repetidos en las columnas de consumo no son stock adicional.
El libro original del proyecto contiene 87 filas: 68 de almacen y 19 de reactivos.
Si vuelve a seleccionar exactamente el mismo archivo, se abre su revision existente mediante su huella SHA-256.

### 11.2 Revisar filas y observaciones

1. Abra el libro desde Libros recibidos si no esta ya en su detalle.
2. Busque por producto o marque Solo pendientes y presione Filtrar.
3. Compare Origen / producto, Lote y fecha originales, Saldo guardado y Observaciones.
4. Despliegue Formula / valor original cuando necesite revisar la procedencia.
5. Presione Revisar en la fila pendiente que va a conciliar.

Las formulas no se ejecutan; un resultado guardado puede ser antiguo o faltar.
Las fechas incompletas, ambiguas o fuera de rango no se corrigen automaticamente.
`S/F` no significa necesariamente que no aplica caducidad; `S/L` tampoco es un lote verificado.
Un lote que Excel convirtio a fecha requiere cotejo con la etiqueta, no una conversion supuesta.

### 11.3 Confirmar un saldo inicial

1. En Confirmar saldo inicial, revise la evidencia y las observaciones de la fila.
2. Seleccione una ficha correcta del catalogo. Si no existe, use Registrar producto en catalogo,
   cree la ficha y vuelva al libro para abrir nuevamente la fila.
3. Coteje fisicamente y capture lote, caducidad, ubicacion, cajas/envases y contenido por presentacion.
4. Documente el motivo, por ejemplo Saldo inicial conciliado con conteo fisico.
5. Marque Datos y saldo fisico verificados y presione Confirmar e ingresar saldo.

Resultado: se genera una entrada actual, vinculada a archivo, hoja, fila y responsable; la fila aparece Confirmado.
No se inventan fechas ni responsables de movimientos historicos. La fila ya resuelta no se importa otra vez.
Una importacion de saldo inicial se bloquea si ese producto/lote ya tiene existencias registradas,
incluso si procede de otro archivo. Una diferencia de caducidad/ubicacion tambien requiere conciliacion.
No intente evadir el bloqueo renombrando el lote o el producto.

### 11.4 Omitir una fila duplicada o no aplicable

1. Abra Revisar en la fila que no debe generar existencias.
2. Despliegue Omitir fila sin generar existencias.
3. Escriba Motivo de omision / referencia de conciliacion.
4. Presione Omitir y registrar motivo.

Resultado: la fila queda Omitido, con su motivo y auditoria; el saldo no cambia y deja de contarse como pendiente.
Por ejemplo, despues de confirmar el saldo fisico total de un duplicado en una sola fila, documente en la otra
la referencia de conciliacion. No sume ambas filas sin comprobar el material real.
La version actual no ofrece reapertura de filas confirmadas u omitidas; revise antes de resolver.

## 12. Alertas de caducidad y notificaciones

1. Abra Alertas.
2. Revise partidas con saldo y caducidad efectiva dentro de 90 dias, incluidos vencidos.
3. Abra el detalle para decidir consumo FEFO, cuarentena o baja segun permisos y procedimientos.
4. Revise Notificaciones de correo: fecha, asunto, estado, intentos y detalle.

La pantalla se calcula con los datos actuales. Abrirla no genera ni envia correos: eso lo hace el comando
`process_alerts` o su tarea programada. Las partidas agotadas no generan alertas de caducidad.
Un material en cuarentena puede seguir visible en Alertas, aunque la generacion de correo de caducidad
solo considera lotes aceptados. Los avisos de minimo se consultan tambien en Resumen y en la cola cuando se generan.
La lista de notificaciones muestra los 30 registros mas recientes.

| Estado de correo | Significado y accion |
| --- | --- |
| Pendiente | Registrado en cola; aun no procesado para envio |
| En proceso | Un proceso tomo el mensaje; no lance otro envio manual del mismo aviso |
| Aceptado por Microsoft | Microsoft acepto la solicitud; no garantiza entrega al destinatario |
| Reintentable | Fallo que admite reintento programado; revise el detalle y la configuracion |
| Resultado incierto | Puede haberse enviado; revise Elementos enviados antes de intervenir. No se reenvia automaticamente |
| Cancelado | La alerta dejo de aplicar, hubo un rechazo no reintentable o se agotaron los intentos; revise Detalle |

No hay botones de reenvio o resolucion manual de estados de la cola en esta version.
No prometa que un destinatario recibio el mensaje solo porque el estado sea Aceptado por Microsoft.

## 13. Configurar correo Microsoft personal

Disponible para Responsable y Superusuario. Requiere buzon compatible con Microsoft Graph, registro
de aplicacion y autorizacion personal; el procedimiento tecnico completo esta en [README.md](README.md).

1. Desde Alertas presione Configurar correo.
2. Capture ID publico de aplicacion Microsoft, no un secreto ni una contrasena.
3. Escriba los Destinatarios, uno por linea; se admiten hasta 20 direcciones distintas.
4. Deje Habilitar notificaciones por correo desmarcado en la preparacion inicial.
5. Presione Guardar configuracion.
6. Realice personalmente `manage.py connect_mail` con el Python de `.venv`, siguiendo el enlace oficial Microsoft.
7. Vuelva a esta pantalla, marque Habilitar notificaciones por correo y guarde.
8. Haga una prueba controlada mediante los comandos documentados y revise Alertas y el buzon destinatario.

Resultado del formulario: se guardan configuracion y auditoria. No inicia sesion en Microsoft ni envia un mensaje.
La indicacion Habilitado solo refleja la configuracion; no demuestra que el token Microsoft siga vigente.
Para habilitar deben existir ID y destinatarios validos. Elimine la marca y guarde para detener nuevos envios
del procesador; cerrar el navegador no deshabilita el correo. La cola conserva su historial y destinatarios previos.

## 14. Administracion de usuarios

El enlace Administracion de usuarios aparece al Superusuario. La administracion abre una interfaz separada.

1. Abra `/admin/` con el superusuario creado en el alta inicial.
2. Entre a Usuarios y elija la opcion para agregar un usuario.
3. Complete usuario y contrasena segun el formulario y guarde.
4. Abra la ficha creada, compruebe Activo y asigne uno de los grupos Auditor, Operador o Responsable.
5. Guarde y pruebe el acceso con esa cuenta en otra sesion de navegador.

No active Superusuario para usuarios normales ni asigne permisos de personal/staff solo para consultar inventario.
Si combina grupos, sus permisos se acumulan; no use varios grupos para intentar restringir acceso.
Para retirar acceso, desactive la cuenta en lugar de borrar un responsable que tenga movimientos historicos.
El cambio de contrasena de un usuario se realiza desde su ficha en la administracion.
Los registros del inventario estan registrados como solo lectura en `/admin/`: no se corrigen saldos alli.

## 15. Recorridos completos recomendados

### Arranque del laboratorio

1. Inicie la aplicacion y cree el administrador inicial.
2. Cree las cuentas y asigne roles.
3. Registre las fichas con unidades, equivalencias y caducidad correctas.
4. Prepare el Excel, concilie cada saldo y omita duplicados con motivo.
5. Registre aperturas reales de envases ya abiertos cuando corresponda.
6. Contraste Resumen, Existencias y Movimientos con el inventario fisico.
7. Configure y pruebe correo; despues configure tareas y respaldos conforme a [README.md](README.md).

### Recepcion y consumo diario

1. Busque el producto en Catalogo; el responsable crea la ficha si falta.
2. Registre la entrada verificada.
3. En Existencias seleccione la partida util con caducidad mas cercana.
4. Registre apertura, si corresponde, y luego consumo en unidad base.
5. Confirme saldo posterior e historial; al terminar, cierre sesion.

### Material vencido o en investigacion

1. Identifique la partida desde Alertas o Existencias.
2. Un responsable establece Cuarentena con motivo si debe investigarse.
3. Registre Baja si se retira material, conforme al procedimiento del laboratorio.
4. Verifique saldo e historial; no use un consumo para simular una baja.

### Error de captura de una salida

1. Localice el movimiento equivocado.
2. Un responsable revierte la salida con motivo.
3. Capture el movimiento correcto y contraste saldo e historial.
4. Si el error afecta ficha, entrada, lote, caducidad o apertura, esta version no ofrece una correccion general;
   solicite revision al responsable antes de registrar operaciones compensatorias.

## 16. Limites y soporte

No hay pantallas para respaldar/restaurar, registrar tareas Windows, autorizar Microsoft, manejar HDS/adjuntos,
generar QR, editar fichas existentes o borrar movimientos. No documente esos pasos como botones disponibles.
Los procedimientos tecnicos que si existen se ejecutan fuera del navegador y estan en [README.md](README.md).
El sistema apoya la trazabilidad, pero no certifica cumplimiento normativo ni decide compatibilidad quimica.

Ante un error, conserve la pantalla y el mensaje, anote partida/lote, accion y hora, y contacte al responsable.
No borre `data`, no edite SQLite y no repita entradas para forzar un saldo. Antes de una intervencion tecnica,
genere un respaldo. No comparta por chat contrasenas, tokens, claves locales ni bases con informacion del laboratorio.