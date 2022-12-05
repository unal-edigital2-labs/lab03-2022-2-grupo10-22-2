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
Para describir la camara, mas presisamente la imagen que ella va a tomar, ademas de conocer el modelo del dispositivos, tambien hay que tomar en cuenta las limitaciones del sistema que restringen lo que podemos o no hacer.

Iniciando con el tema memoria, la nexys A7 tiene integrado 1188000 bits para memoria, ahora, si quisieramos mostrar una imagen con toda la resolucion y tamaño que nos permite la camara, necesitariamos almacenar en memoria, 640*480=307200 pixeles, la informacion de estos pixeles viene dada por sus componentes RGB, los cuales tienen  diferentes formatos dependiendo la profundidad en el color que se quiera, sin embargo, en nuestro caso nos vemos limitados a 4 bits por color, es decir RGB444, esto debido a que es el limite que soporta el conector vinculado a la nexys.

Siendo esto asi, si quisieramos mostrar una imagen con el maximo tamaño resolucion y color posible, necesitariamos 307200*12=3686400 bits, cifra que supera por mucho los recursos con los que contamos,por esta razon se opto por reducir el tamaño de la imagen manteniendo la profundidad de color, esto pues se consifero que de por si RGB444 ya tiene una muy pobre profundidad de color.

Bajando la resolucion a la mitad, se ve se el consumo de bits baja bastante, sin embargo roza el Mbit, lo que nos deja con poco espacio para almacenar mas informacion, por tanto, se decidio bajar la resolucion a la mitad otra vez, es decir dividirla en 4,quedando un formato de 160*120, con un formato de color RGB444.

Con esta resolucion, se tiene que se deben guardar 19200 pixeles de 12 bits cada uno, asi, el tamaño en bits de posiciones de mi memoria sera 2^n=19200, que despejando n, nos da aproximadamente 14.2 bits, pero como no hay medios bits, se aproxima aal entero mayor mas cercano, es decir, que se necesitaran 15 bits para describir la posicon en memoria
