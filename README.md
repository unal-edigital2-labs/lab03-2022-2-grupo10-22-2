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

Con esta resolucion, se tiene que se deben guardar 19200 pixeles de 12 bits cada uno, asi, el tamaño en bits de posiciones de mi memoria sera 2^n=19200, que despejando n, nos da aproximadamente 14.2 bits, pero como no hay medios bits, se aproxima aal entero mayor mas cercano, es decir, que se necesitaran 15 bits para describir la posicon en memoria.

## Cam_read
Teniendo ya la informacion de la imagen a tomar, se procede a diseñar las conexiones mediante verilog de como va a a funcionar el modulo de la camara.
Debido a que la camara no posee memoria, lo primero que se ha de hacer es almacenar los datos en una memoria, de eso se hara cargo parcialmente cam_read.v, el cual lee los pines de datos a la frecuencia que dicte un reloj de entrada al modulo y lo manda al modulo de memoria ram.

En este archivo tambien nos encargamos de unir los datos que saca la camara y mandarlos a la memoria donde los almacenaremos, esto lo hacemos mediante 2 registros de salida, que junto a 1 registro de habilitacion componen las salidas de este modulo.
Nota: Cabe aclarar que este modulo posee una maquina de 3 estados dependiendo el estado de lectura de la camara, esto pues al tener solo 8 pines de datos pero como el pixel tiene 12, debe pasar los datos en 2 tandas, le la primera manda todo el rojo, en la segunda verde y aul, de eso se encrgar cam_read.

El codigo de este archivo es el siguiente:

```
module cam_read #(
		parameter AW = 15,  // Cantidad de bits  de la direcci�n
		parameter DW = 12   //tamaño de la data 
		)
		(

		CAM_pclk,     //reloj 
		CAM_vsync,    //Señal Vsync para captura de datos
		CAM_href,	// Señal Href para la captura de datos
		rst,		//reset
		
		DP_RAM_regW, 	//Control de esctritura
		DP_RAM_addr_in,	//Dirección de memoria de entrada
		DP_RAM_data_in,	//Data de entrada a la RAM
		CAM_px_data
	    );
	
	    input [7:0]CAM_px_data;
	    
		input CAM_pclk;		//Reloj de la camara
		input CAM_vsync;	//señal vsync de la camara
		input CAM_href;		//señal href de la camara
		input rst;		//reset de la camara 
		
		output reg DP_RAM_regW; 		//Registro del control de escritura 
	    output reg [AW-1:0] DP_RAM_addr_in;	// Registro de salida de la dirección de memoria de entrada 
	    output reg [DW-1:0] DP_RAM_data_in;	// Registro de salida de la data a escribir en memoria
        
        
//Maquina de estados	
	
localparam INIT=0,BYTE1=1,BYTE2=2,NOTHING=3,imaSiz=19199;
reg [1:0]status=0;

always @(posedge CAM_pclk)begin
    if(rst)begin
        status<=0;
        DP_RAM_data_in<=0;
        DP_RAM_addr_in<=0;
        DP_RAM_regW<=0;
    end
    else begin
	    
     case (status)
         INIT:begin 
             if(~CAM_vsync&CAM_href)begin // cuando la señal vsync negada y href son, se empieza con la escritura de los datos en memoria.
                 status<=BYTE2;
                 DP_RAM_data_in[11:8]<=CAM_px_data[3:0]; //se asignan los 4 bits menos significativos de la información que da la camara a los 4 bits mas significativos del dato a escribir
             end
             else begin
                 DP_RAM_data_in<=0;
                 DP_RAM_addr_in<=0;
                 DP_RAM_regW<=0;
             end 
         end
         
         BYTE1:begin
             DP_RAM_regW<=0; 					//Desactiva la escritura en memoria 
             if(CAM_href)begin					//si la señal Href esta arriva, evalua si ya llego a la ultima posicion en memoria
                     if(DP_RAM_addr_in==imaSiz) DP_RAM_addr_in<=0;			//Si ya llego al final, reinicia la posición en memoria. 
                     else DP_RAM_addr_in<=DP_RAM_addr_in+1;	//Si aun no ha llegado a la ultima posición sigue recorriendo los espacios en memoria y luego escribe en ellos cuan do pasa al estado Byte2
                 DP_RAM_data_in[11:8]<=CAM_px_data[3:0];
                 status<=BYTE2;
             end
             else status<=NOTHING;   
         end
         
         BYTE2:begin							//En este estado se habilita la escritura en memoria
             	DP_RAM_data_in[7:0]<=CAM_px_data;
             	DP_RAM_regW<=1;    
             	status<=BYTE1;
         end
         
         NOTHING:begin						// es un estado de trnsición    
             if(CAM_href)begin					// verifica la señal href y se asigna los 4 bits mas significativos y se mueve una posición en memoria
                 status<=BYTE2;
                 DP_RAM_data_in[11:8]<=CAM_px_data[3:0];
                 DP_RAM_addr_in<=DP_RAM_addr_in+1;
             end
             else if (CAM_vsync) status<=INIT;		// Si vsync esta arriba inicializa la maquina de estados    
         end
         
         default: status<=INIT;
    endcase
 end
end
```
