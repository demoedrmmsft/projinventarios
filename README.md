# Lote LAB

Inventario local de laboratorio para Windows, Python 3.13, Django 5.2 LTS y SQLite.
La aplicacion solo escucha en `127.0.0.1`. No requiere Azure ni una base de datos en la nube.
Zona horaria de negocio: `America/Mexico_City` (CDMX, UTC-6 actualmente).

## Inicio

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\Start-Lab.ps1
```

Abra http://127.0.0.1:8000/. En la primera visita se solicita crear el administrador.
La contrasena se introduce exclusivamente en el navegador y se almacena con el hash de Django.
El alta inicial se cierra cuando existe el primer usuario. No hay credenciales predeterminadas.
Si el puerto esta ocupado, use `Start-Lab.ps1 -Port 8001`.
El servidor debe permanecer en ejecucion. No lo exponga a la red o Internet.

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

Desde `/admin/` cree cuentas y asigne un grupo. No use una cuenta compartida.

| Rol | Acceso |
| --- | --- |
| Auditor | Consulta y exportacion; sin movimientos |
| Operador | Consulta, entradas, aperturas y consumos |
| Responsable | Lo anterior, catalogo, importaciones, bajas, reversiones y configuracion de correo |
| Superusuario | Todo lo anterior y administracion de usuarios |

Los permisos se verifican en servidor; ocultar botones no es el control de seguridad.
Los registros de inventario se muestran solo en lectura desde el administrador para impedir ediciones directas de saldos.
Los administradores del sistema operativo tienen acceso a SQLite; no es una bitacora a prueba de manipulacion fisica.
Use cuentas Windows separadas, bloqueo de sesion, BitLocker y permisos NTFS restringidos para `data` y `backups`.

## Correo Microsoft personal

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

Recursos visuales locales: Lucide 0.468.0 (ISC, https://lucide.dev/license), fotografia de laboratorio de Unsplash
(https://images.unsplash.com/photo-1579154204601-01588f351e67). Ninguna pantalla depende de un CDN en ejecucion.