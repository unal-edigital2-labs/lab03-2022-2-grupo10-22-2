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

Nota: Como aclaro hace poco, esta camara tiene unos registros internos configurables mediante I2C, nosotros esta parte de configuracion la decidimos hacer mediante arduino ya que por internet ya hay plantillas para la configuracion del periferico, y decidimos no gastar tiempo diseñando la configuracion por verilog, pues despues de cargar la configuracion, se puede desconectar el arduino mientras no se le quite la alimentacion a la camara.

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
## Memoria
Como ya se anañizo anteriormente, para guardar el frame de la camara necesitaremos una memoria de 2^15 posiciones para alcanzar a cubrir todos los bits de informacion de la imagen, y cada uno de estas posiciones deberan tener 12 bits para almacenar el color completo del pixel.
Lo anterior lo logramos mediante un registro matricial de 2^15 * 12 bits, el cual definimos en este archivo con el nombre de ram. Con este registro lo que se busca es guardar la informacion de la imagen que tomo la camara, es decir escribirla en memoria, para lo cual requeriremos 2 entradas, una para definirle una direccion y una para definirle un valor dentro de ram.

Sumado a lo anterior, ese modulo tiene la caracteristica de ser de doble canal, es decir que se puede leer y escribir al mismo tiempo, para añadir la funcion de lectura, añadimos 2 registros de salida, 1 para direccion y 1 para datos, los cuales mas adelante usaremos para definir la imagen a procesar.

Nota: Cabe aclarar que la lectura y escritura de la memoria se hacen en base a 2 relojes distintos, los relojes de la VGA y de la camara respectivamente, esto pues estos tiempos  son los que nos describen cuando se quiere leer un dato y cuando se quere escribir uno, pues la camara es la que proporciona los datos y la VGA la que los consume.

El codigo que describe la memoria es el siguiente:

```
module buffer_ram_dp#(
	parameter AW = 15,		 // Cantidad de bits  de la direccion.
	parameter DW = 12,		 // Cantidad de Bits de los datos.
	// Absolute address in Esteban's computer
	parameter imageFILE = "/LabsDigital2/lab03-2022-2-grupo10-22-2-main/SocProject/sw/module/verilog/camara/imagen.men")
	
	(
	input clk_w,     		 // Frecuencia de toma de datos de cada pixel.
	input [AW-1: 0] addr_in, // Direccion de entrada dada por la camara.
	input [DW-1: 0] data_in, // Datos que entran de la camara.
	input regwrite,		  	 // Enable.

	input clk_r, 				    // Reloj 25MHz VGA.
	input [AW-1: 0] addr_out, 		// DirecciÃon de salida dada por VGA.
	output reg [DW-1: 0] data_out,	// Datos enviados a salida.
	output reg [AW-1: 0] dirc_out	// Direccion de datos enviados a salida.
	);

// Calcular el numero de posiciones totales de memoria.
localparam NPOS = 2 ** AW; 			// Memoria.
localparam imaSiz=160*120;
reg [DW-1: 0] ram [0: NPOS-1];
// Escritura  de la memoria port 1.
always @(posedge clk_w) begin
       if (regwrite == 1)
// Escribe los datos de entrada en la direcciÃ³n que addr_in se lo indique.
             ram[addr_in] <= data_in;
end

// Lectura  de la memoria port 2.
always @(posedge clk_r) begin
// Se leen los datos de las direcciones addr_out y se sacan en data_out.
		data_out <= ram[addr_out];
		dirc_out <= addr_out;
end

// Precargar un archivo hexadecimal en la memoria al momento de cargar el bitstream en la FPGA
initial begin
// Lee en hexadecimal (readmemb lee en binario) dentro de ram [1, pÃ¡g 217].
	$readmemh(imageFILE, ram);
	// En la posición n+1 (160*120) se guarda el color negro
	ram[imaSiz] = 12'h0;
	ram[15'hffff] = 12'h0; // Necesario par el procesamiento
end
endmodule
```

## VGA_driver
VGA_driver, como su nomre lo indica, es el "driver" o codigo que nos intrepreta los bits y nos genera las señales de sincronizacion y datos en el formato que los entienda la pantalla VGA, para esto se hacen los calculos de timings para una pantalla 640x480 y se le asignan los resultados a las señales de salida que usara la pantalla para sincronizarse y mostrar los datos.

El modulo como entrada tiene las señales de reloj, reset y los datos, y como salida nos arroja la sincronizacion vertical y horizontal y el valor del pixel en un formato de salida de 12 bits que mas adelante se descompondra por pines para llevarlos al conector VGA.

El codigo de referencia que usamos es el siguiente

```
module VGA_Driver #(DW = 12) (
	input rst,
	input clk, 						// 25MHz  para 60 hz de 640x480
	input  [DW - 1 : 0] pixelIn, 	// entrada del valor de color  pixel 
	
	output  [DW - 1 : 0] pixelOut, // salida del valor pixel a la VGA 
	output  Hsync_n,		// señal de sincronización en horizontal negada
	output  Vsync_n,		// señal de sincronización en vertical negada 
	output  [9:0] posX, 	// posicion en horizontal del pixel siguiente
	output  [9:0] posY 		// posicion en vertical  del pixel siguiente
);

localparam SCREEN_X = 640; 	// tamaño de la pantalla visible en horizontal 
localparam FRONT_PORCH_X =16;  
localparam SYNC_PULSE_X = 96;
localparam BACK_PORCH_X = 48;
localparam TOTAL_SCREEN_X = SCREEN_X+FRONT_PORCH_X+SYNC_PULSE_X+BACK_PORCH_X; 	// total pixel pantalla en horizontal 


localparam SCREEN_Y = 480; 	// tamaño de la pantalla visible en Vertical 
localparam FRONT_PORCH_Y =10;  
localparam SYNC_PULSE_Y = 2;
localparam BACK_PORCH_Y = 33;
localparam TOTAL_SCREEN_Y = SCREEN_Y+FRONT_PORCH_Y+SYNC_PULSE_Y+BACK_PORCH_Y; 	// total pixel pantalla en Vertical 


reg  [9:0] countX; // tamaño de 10 bits
reg  [9:0] countY; // tamaño de 10 bits

assign posX    = countX;
assign posY    = countY;

assign pixelOut = (countX<SCREEN_X) ? (pixelIn ) : (12'b0) ;

// señales de sincrinización de la VGA.
assign Hsync_n = ~((countX>=SCREEN_X+FRONT_PORCH_X) && (countX<SCREEN_X+SYNC_PULSE_X+FRONT_PORCH_X)); 
assign Vsync_n = ~((countY>=SCREEN_Y+FRONT_PORCH_Y) && (countY<SCREEN_Y+FRONT_PORCH_Y+SYNC_PULSE_Y));


always @(posedge clk) begin
	if (rst) begin
		countX <= (SCREEN_X+FRONT_PORCH_X-1);
		countY <= (SCREEN_Y+FRONT_PORCH_Y-1);
	end
	else begin 
		if (countX >= (TOTAL_SCREEN_X-1)) begin
			countX <= 0;
			if (countY >= (TOTAL_SCREEN_Y-1)) begin
				countY <= 0;
			end 
			else begin
				countY <= countY + 1;
			end
		end 
		else begin
			countX <= countX + 1;
			countY <= countY;
		end
	end
end

endmodule
```
## camara.v
Camara.v es el archivo top de los perifericos, desde donde se instancian cada uno de los modulos anteriormente explicados y desde donde se obtienen los relojes que los manejan.

En este archivo si se describen los pines que seran conectados fisicamente a los componentes, tanto de la camara como de la pantalla VGA, esto pues camara.v sera el puente junto al driver en python que enmascara el verilog para poder trabajarlo mas adelante por software mediante lenguaje C.

Como atributos extra que se le van a instanciar al sistema de verilog a parte de los pines de los perifericos estan 2 puertos tipo wire o cable, data_mem y dir_mem, estos 2 seran tomados como señales de estatus para obtener el valor de los pixeles en memoria mediante el software.

Siendo asi, resumidamente, como ya se menciono mas arriba, este archivo solo se encarga de instanciar los modulos anteriormente creados y hacer las conexiones entre si, para eso definimos varios cables, que conectaran las salidas y entradas de los perifericos entre si.

Nota: Cabe mencionar que se obtuvo otro modulo en verilog que no se explico, el encargado de generar los relojes que usan los prefirericos, clk24_25_nexys4 clk25_24, este se obtuvo usando la herramienta de vivado clocking wizard, esta herramienta nos genero dos relojes derivados del clock principal, uno de 24MHz para el uso de la camara y uno de  25Mhz para el uso de la pantalla, estas señales se conectaron a sus respectivos perifericos mediante wires.

Por ultimo, este verilog tiene una funcion aparte de instanciar y unir los perifericos, y esta es redefinir el direccionamiento a memoria cuando se vayan a mostrar en pantalla pixeles que no tengan un valor definido en memoria, esto para apuntar todos esos valores desconocidos a la ultima posicion de memoria a la cual se le asigno el color negro en el modulo buffer_ram.
