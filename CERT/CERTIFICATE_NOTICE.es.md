# Firma Digital

A partir del 18 de febrero de 2026, todos los ejecutables oficiales distribuidos por PaulNeja (Yo) (PN Security) se encuentran firmados digitalmente mediante un certificado de firma de código propio.

La firma digital cumple las siguientes funciones:

Verificar la integridad del archivo ejecutable.

Permitir comprobar que el binario no fue modificado tras su compilación.

Asociar el ejecutable con una identidad criptográfica concreta.

Proveer trazabilidad sobre compilaciones oficiales.

Permitir validación manual mediante herramientas como signtool o las propiedades de Windows.

---

## Alcance de la firma

La firma digital:

No modifica el funcionamiento del programa.

No agrega dependencias adicionales.

No requiere conexión a Internet para validar la firma básica.

No impide la ejecución en sistemas donde el certificado no esté instalado.

El software funciona correctamente incluso si el certificado no está instalado en el sistema del usuario.

La instalación del certificado es completamente opcional.

---

## Naturaleza del Certificado

El certificado utilizado es un certificado de firma de código autofirmado.

Esto implica que:

No es un certificado emitido por una Autoridad de Certificación comercial.

No elimina automáticamente advertencias de SmartScreen en sistemas externos.

Su propósito principal es garantizar integridad y consistencia de builds oficiales.

La clave privada asociada al certificado no se publica ni se distribuye.

En este repositorio únicamente se incluye el certificado público (.cer).

---

## Instalación Opcional del Certificado en Windows

Instalar el certificado permite que Windows identifique el ejecutable firmado mostrando el nombre del editor en lugar de “Editor desconocido”.

Reiteración importante:
La instalación no es necesaria para utilizar el software.

Método gráfico (recomendado)

Descargar el archivo .cer incluido en el repositorio.

Hacer doble clic sobre el archivo.

Seleccionar “Instalar certificado”.

Elegir “Usuario actual” o "Equipo Local" (Mas recomendado).

Seleccionar “Colocar todos los certificados en el siguiente almacén”.

Elegir “Entidades de certificación raíz de confianza”.

Confirmar la instalación.

Puede requerirse confirmación del sistema.

Método manual alternativo

También puede instalarse mediante consola con herramientas del sistema si el usuario posee conocimientos avanzados.

---

## Verificación de Firma

Para verificar manualmente la firma digital de un ejecutable:

Hacer clic derecho sobre el archivo.

Seleccionar “Propiedades”.

Ir a la pestaña “Firmas digitales”.

Seleccionar la firma correspondiente y visualizar detalles.

También puede verificarse mediante:

signtool verify /pa SentinelDesk.exe

Consideraciones de Seguridad

Instalar un certificado de firma de código implica confiar en la identidad asociada a dicho certificado.

El usuario debe:

Verificar la huella digital (fingerprint) publicada en el repositorio.

Confirmar que el certificado proviene de la fuente oficial.

Instalar únicamente certificados descargados desde el repositorio oficial.

La instalación de certificados no oficiales puede comprometer la seguridad del sistema.

---

## Política de Firma

Todos los ejecutables oficiales distribuidos a partir del 18 de febrero de 2026 se encuentran firmados digitalmente.

La ausencia de firma digital puede indicar:

Compilación no oficial.

Archivo modificado.

Distribución no autorizada.

---

# Huella Digital del Certificado Oficial

Certificado de Firma de Código — PaulNeja (PN Security)
Válido a partir del 18 de febrero de 2026

SHA1
8F61E94560D1B2E621E7DC001F3742E472EAA9EA

SHA256
95BF563120D87ED73CC000CB35BB30173638C4014AA3388DC6BB70CB021EC536

