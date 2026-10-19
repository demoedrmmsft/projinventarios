# Lote LAB

Inventario local de laboratorio para Windows, Python 3.13, Django 5.2 LTS y SQLite.
La aplicacion solo escucha en `127.0.0.1`. No requiere Azure ni una base de datos en la nube.
Zona horaria de negocio: `America/Mexico_City` (CDMX, UTC-6 actualmente).

## Documentacion

- Este README: instalacion, ejecucion, correo, tareas de Windows y respaldos.
- [README_FLUJOS.md](README_FLUJOS.md): instrucciones de todas las pantallas y recorridos de operacion.

## Requisitos

- Windows con Python 3.13 disponible en la terminal y permisos de escritura en la carpeta del proyecto.
- PowerShell y un navegador actualizado, como Edge, Chrome o Firefox.
- Git, solo si descargara el proyecto mediante `git clone`.
- Internet para descargar dependencias y autorizar/enviar correo Microsoft. La operacion local no requiere Internet.

Compruebe Python en PowerShell:

```powershell
python --version
```

La salida debe identificar Python 3.13. Si el comando no se reconoce, instale Python y habilite su acceso desde PATH.

## Instalacion por primera vez

Si todavia no tiene el proyecto, descarguelo con Git y entre en su carpeta:

```powershell
git clone https://github.com/demoedrmmsft/projinventarios.git
Set-Location .\projinventarios
```

Si Git solicita acceso, complete la autenticacion en el navegador con una cuenta autorizada para ese repositorio.
No escriba la contrasena de GitHub en el comando ni coloque tokens en la URL. Si ya existe una carpeta
`projinventarios`, compruebe su contenido antes de intentar clonar; no la borre ni clone dentro de ella por accidente.

#### Opcion B: descargar ZIP sin instalar Git

1. Abra https://github.com/demoedrmmsft/projinventarios en el navegador e inicie sesion si es necesario.
2. Seleccione la rama `main` en GitHub y presione Code > Download ZIP.
3. En el Explorador de archivos de Windows, abra Descargas, haga clic derecho en el ZIP y seleccione Extraer todo.
   No ejecute el proyecto desde la vista del archivo comprimido.
4. Coloque la carpeta extraida en una carpeta local donde pueda escribir, por ejemplo
   `source\repos` dentro de su perfil. El nombre que normalmente genera GitHub es `projinventarios-main`.
5. Abra la carpeta que contiene directamente [manage.py](manage.py) y [requirements.txt](requirements.txt).
   Si hay otra carpeta anidada, entre en ella; esa es la raiz que debe usar.
6. En esa carpeta, use clic derecho > Abrir en Terminal, seleccionando PowerShell, o abra PowerShell
   y cambie a la ruta donde extrajo el proyecto. Si uso el ejemplo anterior:

```powershell
Set-Location "$HOME\source\repos\projinventarios-main"
```

La carpeta del ZIP no tiene historial Git; para actualizaciones tendra que descargar una nueva version.
Conserve sus datos y genere un respaldo antes de cambiar de version; no extraiga otra descarga encima de `data`.

#### Comprobar la carpeta del proyecto

Si ya esta trabajando en este proyecto, no necesita clonarlo otra vez. Abra una terminal en su carpeta raiz,
la que contiene [manage.py](manage.py) y [requirements.txt](requirements.txt).

```powershell
Get-Location
Test-Path .\manage.py
Test-Path .\requirements.txt
```

Las dos comprobaciones deben mostrar `True`. Si muestran `False`, cambie a la carpeta correcta antes de continuar.
Use comillas alrededor de las rutas que tengan espacios. Evite `Program Files`, carpetas de sistema,
unidades de red y carpetas sincronizadas: la base SQLite debe permanecer en un directorio local escribible.

### 4. Instalar dependencias y crear la base local

Prepare el entorno e inicialice la base:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
```

No necesita activar el entorno: los comandos usan directamente su ejecutable Python.
`migrate` crea las tablas; no carga el Excel ni genera existencias.
`check` debe terminar sin errores. Si una instalacion falla, resuelva el error antes de seguir al siguiente paso.

Si tiene varias versiones de Python, cree el entorno con `py -3.13 -m venv .venv`, como se indico arriba.
Compruebe el entorno creado:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip check
```

Debe mostrar Python 3.13.x y no reportar dependencias incompatibles. La descarga de bibliotecas requiere Internet;
si la red del equipo bloquea pip, solicite apoyo al administrador, sin desactivar certificados o antivirus.
No copie `.venv` de otra computadora: cree el entorno e instale las dependencias en la maquina de destino.

Descargar el codigo no descarga los usuarios ni el inventario de otra computadora. Una instalacion nueva comienza
vacia; si esta migrando una instalacion existente, use el procedimiento de Respaldo y restauracion de este README
antes de crear cuentas o cargar existencias nuevas. La autorizacion Microsoft puede requerirse de nuevo en el equipo destino.

## Ejecutar la aplicacion

Desde la carpeta raiz, inicie el servidor:

```powershell
.\Start-Lab.ps1
```

Si PowerShell bloquea scripts por la politica del equipo, use el ejecutable directamente, sin cambiar esa politica:

```powershell
.\.venv\Scripts\python.exe serve.py
```

Abra http://127.0.0.1:8000/. En la primera visita sera redirigido a `/setup/` para crear el administrador.
La contrasena se introduce exclusivamente en el navegador y se almacena con el hash de Django.
El alta inicial se cierra cuando existe el primer usuario. No hay credenciales predeterminadas.

### Comprobar el primer arranque

1. Compruebe que la terminal no muestra errores y deje el servidor en ejecucion.
2. Abra http://127.0.0.1:8000/ en esta misma computadora; `127.0.0.1` no sirve para conectarse desde otro equipo.
3. En una instalacion vacia, cree el administrador en la pantalla de alta inicial y guarde sus credenciales de forma segura.
4. Compruebe que abre Resumen con cero productos y existencias. Eso es normal: no hay una carga automatica del Excel.
5. Siga [README_FLUJOS.md](README_FLUJOS.md) para crear usuarios, registrar productos y conciliar el inventario.
6. Configure correo y tareas programadas solo despues de verificar la operacion local. No son requisitos para abrir el inventario.

Mantenga abierta la terminal mientras usa la aplicacion. Para detener el servidor manual, presione `Ctrl+C`
en esa terminal. Cerrar el navegador no detiene el servidor. No lo exponga a la red o Internet.

Si el puerto esta ocupado, no inicie otra copia sobre el mismo puerto. Compruebe si la aplicacion ya esta
abierta o use temporalmente otro puerto:

```powershell
.\Start-Lab.ps1 -Port 8001
```

Alternativa sin ejecutar scripts PowerShell:

```powershell
$env:LAB_PORT = '8001'
.\.venv\Scripts\python.exe serve.py
```

En ese caso abra http://127.0.0.1:8001/. El puerto alternativo no cambia la base de datos.
Las tareas automaticas descritas mas adelante usan el puerto 8000.

### Uso diario

1. Abra PowerShell en la carpeta del proyecto.
2. Ejecute `.\Start-Lab.ps1`, salvo que la tarea automatica ya haya iniciado el servidor.
3. Abra http://127.0.0.1:8000/ e inicie sesion.
4. Siga los recorridos de [README_FLUJOS.md](README_FLUJOS.md).
5. Cierre sesion al terminar. Si el servidor se inicio manualmente y ya no se utilizara, detengalo con `Ctrl+C`.

No vuelva a crear `.venv` ni a cargar el Excel cada dia. Los registros persisten entre reinicios.

### Archivos locales que deben conservarse

| Ruta | Contenido |
| --- | --- |
| `data/inventory.sqlite3` | Usuarios, productos, saldos, movimientos, revisiones y configuracion de correo |
| `data/secret.key` | Clave local de Django; se crea automaticamente, no se comparte |
| `data/microsoft-cache.bin` | Autorizacion Microsoft protegida para el usuario Windows que la realizo |
| `backups/` | Respaldos generados por el comando o la tarea programada |

Estos archivos estan excluidos de Git. No borre `data` para solucionar problemas: eliminaria la informacion local.
La variable avanzada `LAB_DATA_DIR` cambia la carpeta de datos; dejela sin definir para la operacion normal.

## Alcance entregado

- Resumen, catalogo, lotes, ubicaciones, envases y existencias ordenadas por FEFO.
- Entradas, apertura, consumo parcial, baja y reversion de salidas sin borrar el original.
- Consulta de movimientos, responsables, auditoria y exportacion CSV protegida contra formulas.
- Bloqueo en cada consumo: vencimiento, falta de fecha obligatoria, cuarentena y saldo insuficiente.
- Revision de Excel fila por fila, con procedencia y confirmacion individual del saldo fisico.
- Alertas de 30/60/90 dias, vencidos y existencias minimas; correo personal Microsoft mediante OAuth.
- Comando de respaldo consistente y verificacion de lectura del archivo restaurado.

El alcance no incluye validacion clinica o certificacion normativa. No infiere compatibilidad quimica.
HDS/documentos adjuntos, QR, proveedores, edicion auditada de fichas y reportes avanzados quedan para la siguiente etapa.
No hay datos ficticios en la base operativa ni importacion automatica de existencias.

## Presentaciones y saldos

La equivalencia se define por producto, no globalmente. Se tomo "5 cajas con 100 piezas" como
100 piezas por caja: una entrada de 5 x 100 da 500 piezas. Confirme esta equivalencia por producto
durante la conciliacion; el Excel no basta para inferirla.

La unidad base puede ser piezas, mL o gramos. Piezas admite solo enteros; mL y gramos, hasta tres decimales.
Las presentaciones y la unidad se fijan al crear la ficha. No se cambia la unidad de saldos existentes.
Los frascos de mL conservan saldos individuales: cinco frascos de 500 mL crean cinco registros de 500 mL.
Piezas y gramos se agregan en una partida por entrada. Un frasco de 500 mL menos 12.5 mL conserva 487.5 mL.
La capacidad indicada en "JERINGA 10 ML" no implica que ese producto sea inventario liquido.

La apertura no descuenta cantidad. Los dias tras apertura son opcionales y deben proceder del fabricante.
La caducidad efectiva es la menor entre fabricante y apertura mas dias permitidos, incluyendo el dia final.
Si el fabricante establece otra regla, no habilite el producto hasta revisarla.
Se puede ingresar material vencido para documentar su existencia, pero nunca consumirlo.
Las bajas y cambios de estado requieren motivo. Una reversion restaura saldo, no elimina la salida.
FEFO ordena y recomienda; el operador selecciona el envase. Lotes bloqueados nunca son utilizables.

## Excel real

En Revision de Excel seleccione el archivo original `inventario.xlsx` del proyecto (no se modifica).
Se reconocen `INVENTARIO ALMACEN` y `INVENTARIO REACTIVOS`: 68 y 19 filas en el libro revisado.
Se importa solo el bloque izquierdo, no las columnas repetidas para consumo.
Las formulas se conservan como evidencia pero no se ejecutan. El valor guardado puede estar desactualizado.

Una fila en revision no suma existencias. Para confirmarla, cree o seleccione la ficha correcta y coteje
lote, fecha, ubicacion, numero de cajas/envases y contenido fisico. Las cantidades no se rellenan desde las formulas.
`S/F`, `S/L`, fechas ambiguas y lotes convertidos a fecha requieren comprobacion; no se corrigen por adivinacion.
Para material verdaderamente sin lote se requiere un identificador interno documentado; caducidad no aplicable
debe establecerse conscientemente en la ficha, nunca deducirse de `S/F`.

El SHA-256 evita volver a preparar el mismo archivo. Un lote ya cargado bloquea otra importacion de saldo inicial,
incluso desde un archivo diferente. Producto/lote repetido con caducidades distintas debe conciliarse antes de cargar.
Las filas duplicadas o no aplicables pueden omitirse con motivo documentado; quedan visibles y auditadas, sin generar saldo.
No se reconstruyen fechas ni responsables historicos: la confirmacion produce una entrada de saldo inicial actual,
vinculada al archivo, hoja, fila, datos originales y usuario que la confirmo.

## Usuarios

 Windows 10/11 con Python 3.13 y permisos de escritura en la carpeta del proyecto.

| Rol | Acceso |
| --- | --- |
| Auditor | Consulta y exportacion; sin movimientos |
No necesita instalar Django, SQLite, Waitress ni las otras bibliotecas manualmente: Python incluye SQLite
y el comando de dependencias instala las bibliotecas del proyecto. Tampoco necesita Node.js, npm, Docker,
SQL Server, Excel, Azure ni Visual Studio Code para ejecutar la aplicacion. Excel es opcional para inspeccionar el libro original.

## Preparar una computadora Windows desde cero

### 1. Instalar Python 3.13

1. Abra el sitio oficial: https://www.python.org/downloads/windows/.
2. Localice una version Python 3.13.x que ofrezca instalador de Windows; no seleccione otra version mayor
   solo por ser la descarga principal del sitio. La version usada para desarrollar fue Python 3.13.7.
3. En Windows, abra Configuracion > Sistema > Acerca de y consulte Tipo de sistema.
   Descargue Windows installer (64-bit) para equipos Intel/AMD x64, o Windows installer (ARM64) para equipos ARM64.
   No use el paquete embebible, el archivo de codigo fuente ni la version de 32 bits.
4. Ejecute el instalador y marque Add python.exe to PATH. Conserve la instalacion de pip y del lanzador `py`
   cuando se ofrezcan. Puede instalar para su usuario; no necesita una instalacion para todos los usuarios.
5. Complete la instalacion, cierre las terminales anteriores y abra una nueva ventana de PowerShell desde Inicio.
6. Compruebe la version y pip:
| Responsable | Lo anterior, catalogo, importaciones, bajas, reversiones y configuracion de correo |
| Superusuario | Todo lo anterior y administracion de usuarios |

python -m pip --version
Los permisos se verifican en servidor; ocultar botones no es el control de seguridad.
Los registros de inventario se muestran solo en lectura desde el administrador para impedir ediciones directas de saldos.
El primer comando debe mostrar `Python 3.13.x`. No continue si abre Microsoft Store, no se reconoce
o muestra otra version. Si el lanzador esta disponible, compruebe especificamente Python 3.13:

```powershell
py -3.13 --version
py -3.13 -m pip --version
```

Si estos dos comandos funcionan, puede usar `py -3.13 -m venv .venv` en lugar de `python -m venv .venv`
en la preparacion del proyecto. Los comandos posteriores usan el Python del entorno, sin depender de PATH.
Si ninguno funciona, repare la instalacion y PATH; revise tambien los alias de ejecucion de aplicaciones
de Windows si `python` sigue abriendo Microsoft Store. No desinstale otras versiones que necesiten otros programas.

### 2. Instalar Git, solo para descargar mediante Git

Si elegira descargar un ZIP, omita este paso.

1. Descargue Git for Windows desde https://git-scm.com/downloads/win, seleccionando el instalador compatible con su equipo.
2. Ejecute el instalador. En la opcion de PATH, permita usar Git desde la linea de comandos y otras aplicaciones;
   conserve Git Credential Manager si el instalador lo ofrece. Para el resto puede conservar las opciones predeterminadas.
3. Cierre y vuelva a abrir PowerShell.
4. Compruebe que el comando esta disponible:

```powershell
git --version
```

### 3. Descargar el codigo

Repositorio: https://github.com/demoedrmmsft/projinventarios.
Elija solo una de las dos opciones siguientes. Si el repositorio es privado, necesita una cuenta GitHub
con acceso; solicite permiso al propietario antes de continuar. Un mensaje Repository not found puede indicar falta de acceso.

#### Opcion A: clonar con Git
Use cuentas Windows separadas, bloqueo de sesion, BitLocker y permisos NTFS restringidos para `data` y `backups`.
Abra PowerShell, cree una carpeta local dentro de su perfil y descargue el proyecto:

## Correo Microsoft personal
New-Item -ItemType Directory -Force -Path "$HOME\source\repos"
Set-Location "$HOME\source\repos"

Una suscripcion Office personal no basta por si sola: la cuenta debe tener un buzon Outlook.com/Microsoft
compatible con Graph. Un correo externo usado como identidad Microsoft puede no tener ese buzon.
No se utiliza la contrasena de Outlook ni se habilita autenticacion SMTP basica.

1. Registre una aplicacion propia en Microsoft Entra, que admita cuentas Microsoft personales.
   Esto puede requerir acceso a un directorio; una cuenta personal sola no siempre permite registrar aplicaciones.
2. Habilite el flujo de cliente publico y el permiso delegado Microsoft Graph `Mail.Send`.
   No configure secretos ni permisos de aplicacion. La aplicacion usa la autoridad `consumers`.
3. En Alertas > Configurar correo guarde el ID publico y destinatarios, con el envio deshabilitado inicialmente.
4. Ejecute usted mismo en esta computadora:

```powershell
.\.venv\Scripts\python.exe manage.py connect_mail
```

Siga el enlace Microsoft mostrado en la terminal e introduzca alli el codigo; nunca comparta codigos o tokens por chat.
El comando guarda el cache OAuth protegido con DPAPI para el usuario Windows actual, sin enviar mensajes.
Use la misma cuenta Windows en las tareas. Cambiar usuario/computadora exige autorizar nuevamente.
Despues habilite las notificaciones en la pantalla y compruebe primero un destinatario controlado:

```powershell
.\.venv\Scripts\python.exe manage.py process_alerts
.\.venv\Scripts\python.exe manage.py process_alerts --send
```

El primer comando solo prepara la cola; `--send` efectua envios reales.
El envio permanece pendiente de configuracion y prueba con la cuenta del propietario; no se envio correo durante el desarrollo.
La autorizacion puede expirar/revocarse y requerir repetir `connect_mail`.

Cada partida genera una alerta por banda y caducidad, usando solo la banda mas urgente al revisar.
Se omiten partidas agotadas y se cancelan pendientes cuya condicion dejo de aplicar.
Existencia minima usa solo saldo util y genera como maximo una notificacion diaria por producto.
La cola conserva los destinatarios al generarse; cambiar la configuracion afecta nuevas notificaciones.
HTTP 429/5xx permite hasta cinco intentos con espera creciente. Los errores de transporte despues de iniciar
la llamada se marcan inciertos y no se reenvian automaticamente. Revise Elementos enviados si aparece ese estado.
Un HTTP 202 indica aceptacion de Microsoft, no entrega final ni garantia de envio exactamente una vez.

Referencias: https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0
y https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code.

## Operacion automatica Windows

El servidor funciona con Waitress, no con el servidor de desarrollo de Django.
Los scripts no se ejecutaron ni registraron tareas automaticamente durante el desarrollo.
Con Windows configurado en horario CDMX y la sesion del usuario autorizante iniciada, ejecute:

```powershell
.\Install-Tasks.ps1
```

Registra tres tareas limitadas al usuario actual, sin elevacion: servidor al iniciar sesion, alertas cada
15 minutos y respaldo diario a las 18:00 del reloj de Windows. Usa el puerto 8000 y no sobrescribe tareas existentes.
Si la politica del equipo o los permisos impiden registrarlas, configurelas manualmente con su administrador;
no desactive politicas de seguridad. `StartWhenAvailable` permite recuperar ejecuciones omitidas.
No envia correo ni respalda con el equipo apagado, suspendido o sin sesion iniciada. El correo requiere Internet;
el inventario y sus validaciones no lo requieren. Las alertas tras un periodo apagado usan la banda vigente al volver.

## Respaldo y restauracion

```powershell
.\.venv\Scripts\python.exe manage.py backup_inventory
```

Cada ZIP de `backups` contiene una copia consistente de SQLite, la clave local y un manifiesto.
Se verifica integridad antes y despues de extraer una copia de prueba. No incluye tokens Microsoft ni documentos
fuente originales; conserve tambien el Excel/PDF y una copia del proyecto con sus dependencias.
El ZIP contiene datos y una clave sensible: restrinja su acceso y guarde otra copia cifrada fuera de la computadora.
No hay borrado automatico de respaldos; supervise el espacio disponible.

Para restaurar: detenga servidor y tareas, preserve una copia del directorio `data` actual, extraiga el ZIP a
un directorio temporal y verifique `PRAGMA integrity_check` con SQLite. Reemplace exclusivamente
`data/inventory.sqlite3` y `data/secret.key` por los archivos verificados, usando la misma version del proyecto.
Ejecute `manage.py check`, abra el inventario y contraste conteos, saldo y movimientos. Reautorice el correo
si cambia de usuario/equipo y confirme la configuracion antes de reactivar las tareas.
La prueba automatica verifica recuperacion tecnica; la aceptacion del laboratorio requiere un simulacro con datos reales.

## Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py test inventory
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Criterios cubiertos: decimales exactos, piezas enteras, saldo nunca negativo, FEFO, caducidad en cada consumo,
apertura sin descontar, reversion trazable, permisos/CSRF, importaciones sin duplicados, pantallas, correo simulado
y lectura del respaldo restaurado. La prueba del correo real y registro efectivo de tareas requiere configuracion del propietario.

## Problemas frecuentes al ejecutar

| Situacion | Accion |
| --- | --- |
| `python` no se reconoce | Verifique la instalacion de Python 3.13 y PATH; abra una terminal nueva |
| No existe `.venv\Scripts\python.exe` | Ejecute `python -m venv .venv` desde la raiz e instale las dependencias |
| `No module named django` | Use el Python de `.venv` y vuelva a ejecutar la instalacion de [requirements.txt](requirements.txt) |
| Falta una tabla o columna de SQLite | Detenga el servidor manual, respalde los datos existentes y ejecute `manage.py migrate` con el Python de `.venv` |
| El navegador no conecta | Compruebe que el servidor sigue abierto y que la URL usa el puerto mostrado en la terminal |
| El puerto 8000 ya esta en uso | Compruebe si ya hay un servidor activo; de ser necesario use el puerto alternativo documentado |
| PowerShell impide ejecutar un script | Use `.\.venv\Scripts\python.exe serve.py`; no desactive politicas del equipo |
| Acceso denegado o pagina 403 | Confirme que inicio sesion y que su rol permite la accion; revise la guia de pantallas |
| Error CSRF al enviar un formulario | Abra de nuevo la pantalla en la misma URL local, inicie sesion si corresponde y reintente sin reutilizar un formulario antiguo |
| Olvido de contrasena | El responsable del equipo puede usar `.\.venv\Scripts\python.exe manage.py changepassword NOMBRE_USUARIO`; introduzca la contrasena solo en esa terminal |
| No llegan correos | Confirme buzon compatible, autorizacion, destinatarios, envio habilitado, ejecucion de `process_alerts --send` y conexion a Internet |

Si el equipo no permite ejecutar estas acciones con los permisos actuales, solicite apoyo al administrador.
No comparta contrasenas, tokens, caches OAuth, la clave local ni copias de la base por el chat.

Recursos visuales locales: Lucide 0.468.0 (ISC, https://lucide.dev/license), fotografia de laboratorio de Unsplash
(https://images.unsplash.com/photo-1579154204601-01588f351e67). Ninguna pantalla depende de un CDN en ejecucion.