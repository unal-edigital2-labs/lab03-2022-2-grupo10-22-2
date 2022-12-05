# Proyecto final

# Aplicaciones de Vision artificial en un Soc </em>
## Integrantes
- `Carlo Johel Toscano Maldonado`: Ing. Electronica

- `Nicolle Indira`: Ing Electonica

# Introducción

Este proyecto se basa en el diseño de un Soc VexRisc de 32 bits construido y montado en el entorno de Litex.
Este sistema tiene la finalidad de capturar imagenes en tiempo real a travez de una camara, procesarlos mediante librerias de vision artificial como lo pueden ser OpenCv o vision HDL toolbox, y mostrarlos por una salida de video, que en este caso sera una salida en formato VGA.

El Soc final, debera contar ademas con todos los perifericos, modulos, registros y memorias necesarias para su funcionamiento, la explicacion de esto se realizara acontinuación.

# Perifericos
Para este proyecto no se incluyen muchas terminales fisicas a las que conectarse, ya que el nucleo, o el centro del trabajo seran los algoritmos de vision artificial que vayamos a emplear, por esta razon, solo se desarrollaron 2 terminales a conectar, la camara y la salida VGA, perifericos los cuales describimos en verilog debido a la alta dependencia hacia cambios en los relojes que estos tienen para funcionar.

## Camara
Para describir en verilog la camara primero hay que saber cual dispositivo se va a seleccionar.

En este caso nosotros escogimos la camara OV7670, dispositivo sin memoria el cual es capaz hasta de tomar muestras en formatos de hasta 640x480 pixeles, pudiendo ajustar la imagen mediante registros internos de la camara configurables mediante I2C.
### Consideraciones
Para describir la camara, mas presisamente la imagen que ella va a tomar, ademas de conocer el modelo del dispositivos, tambien hay que tomar en cuenta las limitaciones de el sistema que restringen 
