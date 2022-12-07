# Proyecto final

# Aplicaciones de Vision artificial en un Soc </em>
## Integrantes
- `Carlo Johel Toscano Maldonado`: Ing. Electronica

- `Indira Nicolle Pulgar Carreño`: Ing Electonica

# Introducción

Este proyecto se basa en el diseño de un Soc VexRisc de 32 bits construido y montado en el entorno de Litex.
Este sistema tiene la finalidad de capturar imagenes en tiempo real a travez de una camara, procesarlos mediante librerias de vision artificial como lo pueden ser OpenCv o vision HDL toolbox, y mostrarlos por una salida de video, que en este caso sera una salida en formato VGA.

El Soc final, debera contar ademas con todos los perifericos, modulos, registros y memorias necesarias para su funcionamiento, la explicacion de esto se realizara acontinuación.

# Perifericos
Para este proyecto no se incluyen muchas terminales fisicas a las que conectarse, ya que el nucleo, o el centro del trabajo seran los algoritmos de vision artificial que vayamos a emplear, por esta razon, solo se desarrollaron 2 terminales a conectar, la camara y la salida VGA, perifericos los cuales describimos en verilog debido a la alta dependencia hacia cambios en los relojes que estos tienen para funcionar.

## Diseño del system on Chip
(https://raw.githubusercontent.com/Grupo10-22-2/lab03-2022-2-grupo10-22-2/master/DISENO_SOC.PNG)

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
El codigo de camara.v final es:

```
module camara #(
		parameter AW = 15, // Cantidad de bits  de la dirección 
		localparam DW=12 // Se determina de acuerdo al tamaño de la data, formaro RGB444 = 12 bites.
		)(
		//Entradas del test cam
	    	input  clk,           	// Board clock: 100 MHz Nexys4DDR.
    		input  rst,	 	// Reset button. Externo

		// Salida VGA
		output  VGA_Hsync_n,  // Horizontal sync output.
		output  VGA_Vsync_n,  // Vertical sync output.
		output  [3:0] VGA_R,  // 4-bit VGA red output.
		output  [3:0] VGA_G,  // 4-bit VGA green output.
		output  [3:0] VGA_B,  // 4-bit VGA blue output.

		//CAMARA input/output conexiones de la camara 

		output  CAM_xclk,		// System  clock input de la camara.
		output  CAM_pwdn,		// Power down mode.
		input  CAM_pclk,		// Senal PCLK (pixel clock) de la camara. 
		input  CAM_href,		// Senal HREF de la camara. 
		input  CAM_vsync,		// Senal VSYNC de la camara.
		input  [7:0]CAM_px_data,
		wire [DW-1:0] data_mem,    		// Salida de dp_ram al driver VGA y a software
		wire [AW-1:0] dir_mem    		// Salida de dp_ram a software
    
	);


	// TAMANO DE ADQUISICION DE LA CAMARA

	parameter CAM_SCREEN_X = 160; 		// 640 / 4. Elegido por preferencia, menos memoria usada.
	parameter CAM_SCREEN_Y = 120;    	// 480 / 4.
	
	localparam imaSiz= CAM_SCREEN_X*CAM_SCREEN_Y;// Posición n+1 del tamañp del arreglo de pixeles de acuerdo al formato.

	// conexiondes del Clk
	wire clk100M;           // Reloj de un puerto de la Nexys 4 DDR entrada.
	wire clk25M;		// Para guardar el dato del reloj de la Pantalla (VGA 680X240 y DP_RAM).
	wire clk24M;		// Para guardar el dato del reloj de la camara.

	// Conexion dual por ram

	wire [AW-1: 0] DP_RAM_addr_in;		// Conexión  Direccion entrada.
	wire [DW-1: 0] DP_RAM_data_in;      	// Conexion Dato entrada.
	wire DP_RAM_regW;			// Enable escritura de dato en memoria .

	reg [AW-1: 0] DP_RAM_addr_out;		//Registro de la dirección de memoria. 
	// Conexion VGA Driver
	wire [DW-1:0] data_RGB444;  		// salida del driver VGA a la pantalla
	wire [9:0] VGA_posX;			// Determinar la posición en X del pixel en la pantalla 
	wire [9:0] VGA_posY;			// Determinar la posición de Y del pixel en la pantalla


	/* ****************************************************************************
	Asignación de la información de la salida del driver a los pines de la pantalla
	**************************************************************************** */
	assign VGA_R = data_RGB444[11:8]; 	//los 4 bites más significativos corresponden al color ROJO (RED) 
	assign VGA_G = data_RGB444[7:4];  	//los 4 bites siguientes son del color VERDE (GREEN)
	assign VGA_B = data_RGB444[3:0]; 	//los 4 bites menos significativos son del color AZUL(BLUE)
	

	/* ****************************************************************************
	Asignacion de las seales de control xclk pwdn de la camara
	**************************************************************************** */

	assign CAM_xclk = clk24M;		// AsignaciÃ³n reloj cÃ¡mara.
	assign CAM_pwdn = 0;			// Power down mode.
	

	/* ****************************************************************************
	bloque que genera un reloj de 25Mhz usado para el VGA  y un reloj de 24 MHz
	utilizado para la camara, estos a partir de una frecuencia de 100 Mhz que corresponde a la Nexys 4 	
	----->modulo obtenido por clocking wizard<---
	**************************************************************************** */


	clk24_25_nexys4 clk25_24(
	.clk24M(clk24M),
	.clk25M(clk25M),
	.reset(rst),
	.clk100M(clk)
	);


	/* ****************************************************************************
	Modulo de captura de datos  cam_read
	**************************************************************************** */
	
	cam_read #(AW,DW) cam_read
	(
			.CAM_px_data(CAM_px_data),
			.CAM_pclk(CAM_pclk),
			.CAM_vsync(CAM_vsync),
			.CAM_href(CAM_href),
			.rst(rst),

		//outputs
		
			.DP_RAM_regW(DP_RAM_regW), 
			.DP_RAM_addr_in(DP_RAM_addr_in),
			.DP_RAM_data_in(DP_RAM_data_in)

		);


	/* ****************************************************************************
	buffer_ram_dp buffer memoria dual port y reloj de lectura y escritura separados
	**************************************************************************** */

	buffer_ram_dp DP_RAM(
		// Entradas.
		
		.clk_w(CAM_pclk),			// Frecuencia de toma de datos de cada pixel.
		.addr_in(DP_RAM_addr_in), 		// Direccion entrada dada por el capturador.
		.data_in(DP_RAM_data_in),		// Datos que entran de la camara.
		.regwrite(DP_RAM_regW), 	       	// Enable.
		.clk_r(clk25M), 			// Reloj VGA.
		.addr_out(DP_RAM_addr_out),		// Direccion salida dada por VGA.

			// outputs
			
		.data_out(data_mem),		    	// Datos enviados a la VGA y a software
		.dirc_out(dir_mem)			//Direcciones enviadas a software
	);

	/* ****************************************************************************
	VGA_Driver640x480
	**************************************************************************** */
	VGA_Driver VGA_640x480 // driver pantalla.
	(
		.rst(rst),
		.clk(clk25M), 			// 25MHz  para 60 hz de 160x120.
		.pixelIn(data_mem), 		// Entrada del valor de color  pixel RGB 444.
		.pixelOut(data_RGB444),		// Salida de datos a la VGA. (Pixeles). 
		.Hsync_n(VGA_Hsync_n),		// Sennal de sincronizacion en horizontal negada para la VGA.
		.Vsync_n(VGA_Vsync_n),		// Sennal de sincronizacion en vertical negada  para la VGA.
		.posX(VGA_posX), 		// Posicion en horizontal del pixel siguiente.
		.posY(VGA_posY) 		// posicinn en vertical  del pixel siguiente.

	);


	/* ****************************************************************************
	Logica para actualizar el pixel acorde con la buffer de memoria y el pixel de
	VGA si la imagen de la camara es menor que el display VGA, los pixeles
	adicionales seran iguales al color del ultimo pixel de memoria.
	**************************************************************************** */
	always @ (VGA_posX, VGA_posY) begin
			if ((VGA_posX>CAM_SCREEN_X-1)|(VGA_posY>CAM_SCREEN_Y-1))begin
				DP_RAM_addr_out = imaSiz;
			end
			else begin
				DP_RAM_addr_out = VGA_posX + VGA_posY * CAM_SCREEN_X;// Calcula posicion.
			end
	end
endmodule
```
# Camara.py
El codigo que enmascara el verilog para poder trabajar con los perifericos mediante software es Camara.py, este script se encarga de asignar los pines definidos por el constraint o el xdc de la tarjeta que se este utilizando a las entradas y salidas definidas en el verilog; aparte de esto, asigna 2 registros status a los cables conectados a las salidas de datos y direcciones de la memoria para luego desde codigo C poder trabajar u operar sobre ellos.

Al final, instancia todo asignando lo anteriormente dicho obteninedo el siguiente codigo
```
class Camara(Module,AutoCSR):
    def __init__(self, VGA_Vsync_n,VGA_Hsync_n,VGA_R,VGA_G,VGA_B,xclk,CAM_pwdn,pclk,cam_data_in,vsync,href):
        self.clk = ClockSignal() # Reloj global   
        self.rst = ResetSignal() # Reset Global
        
        #VGA
        self.VGA_Vsync_n= VGA_Vsync_n # Sincronización vertical
        self.VGA_Hsync_n= VGA_Hsync_n  # Sincronizacióñ horizontal
        self.VGA_R= VGA_R
        self.VGA_G= VGA_G
        self.VGA_B= VGA_B
        # Cámara
        self.xclk = xclk    # 24 Señal de 24MHz
        self.CAM_pwdn=CAM_pwdn
        self.pclk = pclk     # Reloj de los datos
        self.href = href
        self.vsync = vsync  
        self.px_data = cam_data_in # datos de la cámara
        self.datamem= CSRStatus(16)
        self.dirmem= CSRStatus(16)

        self.specials +=Instance("camara",
            i_clk = self.clk,
            i_rst = self.rst,
            o_VGA_Hsync_n=self.VGA_Hsync_n,
            o_VGA_Vsync_n=self.VGA_Vsync_n,
            o_VGA_R=self.VGA_R,  
            o_VGA_G=self.VGA_G,
            o_VGA_B=self.VGA_B,


            # Camara
            o_data_mem=self.datamem.status,
            o_dir_mem=self.dirmem.status,
            o_CAM_xclk = self.xclk,
            o_CAM_pwdn=self.CAM_pwdn,
            i_CAM_pclk = self.pclk,
            i_CAM_href = href,        
            i_CAM_vsync = vsync,
            i_CAM_px_data=self.px_data,
            

        )
       
        self.submodules.ev = EventManager()
        self.ev.ok = EventSourceProcess()
        self.ev.finalize()
        self.ev.ok.trigger.eq(self.clk)
```
# Build Soc Project
Este codigo en Python se encarga de generar los perifericos en base a los "drivers" hechos en python y los constraint del xdc de la tarjeta, permitiendo luego en codigo modificar o leer los pines mediante funciones predefinidas, haciendo mas facil el trabajo con muchos pines.

Para nuestro Soc, dejamos la definicion de leds, switeches y botones, y añadiños los pines para la VGA y para la camara añadiendo el core o driver anteriormente programado. y "jalado" los pines necesarios para la conexion mediante un identificador dado a los pines en el constraint.

Nota: Cabe mencionar que para usar el core o driver de python hay que añadir los archivos de verilog para que pueda enmascarar la configuracion del periferico, esto se hace mediante Platform.add_source("Direccion_archivo").
# Primeras pruebas
Debido a la configuracion inicial que se le dio a los pines en camara.v, la camara deberia de empezar a trasmitir video tan solo cargado el bitstream, esto se hizo para preliminarmente verificar el funcionamiento de la camara.
##### Link prueba camara :https://drive.google.com/file/d/1YdM5BBfXedZHid7PMzZMwOZvfv5PpUln/view?usp=sharing

# Software
Para las pruebas del software en nuestro soc, usamos los regisros CSR que se comunican con el periferico mediante el bus wishbone, esto para crear una matriz 3d con el valor de color del pixel y con su direccion en memoria.

Para probar esto imprimimos por pantalla el valor guardado a la vez mientras se añadia a la matriz. : https://drive.google.com/file/d/1v4_X1m2oQtQSrvsGDM5UdDI_EJWFdNGP/view?usp=sharing

# Procesos faltantes
Debido a los inconvenientes que se tuvo a lo largo del semestre con la tarjeta inicialmente usada, la zyboZ7 y su incapacidad de mostrar VGA, asi como el desistimiento de compañeros del grupo y incroporacion de nuevos a mitad de semestre, se atraso el avance del proyecto, quedando pendiente generar una matriz 3d con solo los componente RGB del frame capturado, compilar la libreria OpenCv para CPU risc-v, implementarla con la imagen matricial obtenida, asi como tambien modificar camara.V para que lo que muestre VGA sea la imagen que retorne mi software y no los pixeles generados por la camara.
