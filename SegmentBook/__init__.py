import azure.functions as func
import regex as re
import json
import logging
import os

MAX_CHARS_PER_CHUNK = 12000 

def smart_split(text, max_chars):
    # (Tu función smart_split actual está perfecta, no la toques)
    if len(text) <= max_chars:
        return [text]
    chunks = []
    remaining_text = text
    while len(remaining_text) > max_chars:
        split_point = remaining_text.rfind('\n', 0, max_chars)
        if split_point == -1:
            split_point = max_chars
        chunk = remaining_text[:split_point].strip()
        if chunk:
            chunks.append(chunk)
        remaining_text = remaining_text[split_point:].strip()
    if remaining_text:
        chunks.append(remaining_text)
    return chunks

def main(book_path: str):
    try:
        # ... (Tu variable sample_text con el libro va aquí) ...
        sample_text = """
Prólogo
Juan Moreno afinó su guitarra bajo la sombra del laurel que dominaba la plaza de San Guzmán. Era sábado por la noche, y el pueblo había cobrado vida después de una semana de trabajo bajo el sol de finales de agosto del 43. Las mujeres habían sacado sus mejores vestidos, los hombres se habían afeitado y los niños corrían entre las piernas de los adultos mientras sus madres conversaban junto a la fuente.
Cuando la gente vio que Juan finalmente había llegado a la plaza, poco a poco se fueron acercando. Juan se encargó de saludar a cada uno por su nombre.
Tocó los primeros acordes de “La Adelita” y, como cada sábado, la gente comenzó a bailar al son de su guitarra. Primero fueron los Herrera, luego los Vázquez, después las muchachas solteras que fingían no buscarlo con la mirada. En veinte minutos, la mitad del pueblo estaba ahí, algunos bailando, otros solo escuchando.
Su hermano Luis seguramente seguía en la cantina de José Luis, donde a estas horas ya estaría comprando rondas para medio pueblo. Ángel, el menor, estaría en su cuarto con algún libro.
La fiesta seguía con emoción. La gente, poco a poco, se soltaba más, por obra de la música y el alcohol.
Los gritos de felicidad, las risas y el zapateo incesante de la gente inundaban San Guzmán con alegría. Alegría que escaseaba últimamente por culpa de las sequías recientes.
La celebración se vio interrumpida cuando, entre murmullos, la gente se abrió paso para dejar pasar a la bella y joven Fernanda. Hija de Juan Herrera, quien llegó gritando por auxilio.
—¡Juan! —gritó la mujer—. ¡Juan, por favor, ayúdame!
Fernanda llegó hasta la fuente de la plaza y tomó a Juan del brazo, tirando de él suavemente.
—¿Qué pasa? —preguntó Juan mientras dejaba su guitarra a un lado.
—Felipe —dijo la mujer entre jadeos, tomando aire tras la carrera—. Están golpeando a Felipe.
Juan soltó la guitarra de golpe sobre la banca. 
—¿Dónde? 
—En la entrada. Los García. 
Juan ya corría antes de que ella terminara la frase. La gente se apartaba al verle la cara; no era el músico de hacía un minuto, era un Moreno buscando pleito. 
—Lo siento —jadeó Fernanda, intentando seguirle el paso—, yo… estuve saliendo con uno de ellos. 
—Ahorita no importa eso. Las botas de Juan martillaban el empedrado, marcando un ritmo furioso hasta llegar a las últimas casas de San Guzmán.
El sonido de las botas chocando contra el empedrado se vio interrumpido al escuchar fuertes golpes y jadeos más adelante.
Al doblar la última esquina, la imagen de Felipe hecho un ovillo en el suelo recibió al pueblo. Cuatro hombres con la vestimenta típica de los García lo estaban pateando mientras se burlaban de él.
—¡Basta! —bramó Juan con una voz tan fuerte y clara que por un momento paralizó a los atacantes.
Los cuatro García se incorporaron lentamente, sin prisa, como si hubieran estado esperando esta interrupción. El más alto, un hombre de barba descuidada y sombrero desgastado, escupió al suelo cerca de Felipe.
—Vaya, vaya… si no es el mismísimo Juanito Moreno —dijo con una sonrisa torcida—. ¿Vienes a cuidar a tu gente, patrón?
Juan permaneció inmóvil, con los brazos a los costados. Su voz salió fría como el acero.
—Váyanse. Ahora.
—¿O qué? —se burló otro de los García, más joven, dando un paso hacia delante—. ¿Vas a mandar a tus changos a corrernos?
La multitud rugió detrás de Juan. Alguien gritó “¡Sáquenlos del pueblo!” y otros comenzaron a avanzar. Juan alzó la mano sin voltear, y la gente se detuvo.
—No necesito a nadie para enfrentarme a ustedes —dijo Juan, su mirada fija en el García alto—. Pero tampoco quiero ensuciarme las manos en días de fiesta.
El García escupió otra vez, esta vez más cerca de las botas de Juan.
—Claro, el futuro presidente no se ensucia. Que lo hagan otros por él.
—Basta de provocaciones. Dejen al chico —cortó Juan, dando un paso adelante—. Si tienen ganas de pelear, aquí estoy.
El García soltó una carcajada.
—¿El patrón se va a ensuciar las manos? Esto sí que es nuevo. Lo siento, Juanito, pero este tilico se metió con lo que es mío. Y cuando alguien toca lo mío, paga las consecuencias.
—Nicolás, terminamos hace dos meses —interrumpió Fernanda apartándose de la multitud—. ¿Por qué no puedes entenderlo?
—Porque yo no he terminado contigo, princesa. Tú no decides cuándo se acaba esto.
Un murmullo furioso recorrió la multitud. Alguien gritó “¡Desgraciado!” desde atrás.
—Vas a dejar a la chica en paz —cortó Juan, llevándose la mano lentamente a la funda—. Y al muchacho también.
Los cuatro García intercambiaron miradas y sonrieron. El más joven aplaudió con sarcasmo.
—¡Miren nada más! El gran Juan Moreno necesita su fierro para sentirse valiente.
—Papá tiene razón —se burló el barbudo—. Son tan gallitos con sus pistolas porque sin ellas no son nada.
Fue entonces cuando el estruendo de cascos al galope cortó el aire como un trueno. Un jinete se acercaba por el camino principal levantando una nube de polvo.
Juan sonrió al escucharlo. Quitó la mano de la funda y comenzó a caminar hacia atrás lentamente.
La multitud murmuró y se apartó instintivamente. Un hermoso caballo blanco de crines plateadas emergió de la polvareda, su silla de montar brillando con incrustaciones que reflejaban la luz de las antorchas. Las riendas de cuero trenzado se sacudían mientras el animal reducía la velocidad.
Luis Moreno tiró de las riendas con fuerza, haciendo que su caballo se alzara en dos patas como un guerrero de leyenda. Saltó de la montura antes de que el animal tocara el suelo, aterrizando con un golpe seco que hizo eco en el empedrado.
Se quitó el sombrero con teatralidad, se alisó el cabello hacia atrás y clavó la mirada en los García con una sonrisa que prometía problemas.
—Tú, grandulón —dijo señalando al barbudo como si eligiera fruta en el mercado—. Vas a pelear conmigo. Los otros tres payasos solo van a quedarse ahí parados.
Luis caminó con seguridad en dirección a los García, cuando pasó junto a Juan, le dio un par de palmadas en la espalda. Juan respondió con un asentimiento.
El contraste entre Luis y el García barbón era notable. Luis apenas le llegaba al hombro, pero se plantó frente a él como si midiera tres metros. Llevaba su traje charro café claro, con los bordados dorados brillando bajo las antorchas y la chaqueta abierta, dejando ver la camisa arrugada por la cabalgata. Dio un paso al frente, haciendo tintinear las espuelas y presumiendo el lodo de sus botas como si fueran medallas. 
Echó los hombros hacia atrás, infló el pecho como gallo de pelea y sonrió. Sus manos descansaban relajadas a los costados, pero sus ojos oscuros ardían con una intensidad que hizo que varios de los García intercambiaran miradas nerviosas.
—¿Qué pasa, gigante? —dijo Luis con una sonrisa que no llegaba a sus ojos—. ¿Te da miedo pelear con alguien de tu tamaño… o prefieres seguir pateando muchachos en el suelo?
El barbudo soltó una carcajada forzada.
—Mira nada más, el enano quiere jugar a ser hombre.
La multitud contuvo el aliento. Luis se acercó otro paso, inclinando la cabeza hacia atrás para mirar directamente a los ojos de su oponente.
—Soy lo suficientemente hombre para partirte la madre, grandote. La pregunta es… ¿Tú tienes los huevos para pelear sin tus amiguitos?
Juan observaba con precaución desde un costado. Conocía esa mirada en Luis. Conocía lo que venía después, por eso no se molestó en detenerlo.
El barbudo intentó tomar desprevenido a Luis cuando descargó un gancho con toda su fuerza, buscando terminar la pelea de un solo golpe. Luis se echó hacia atrás con elegancia, arqueando la espalda como un torero esquivando la embestida. El puño del gigante le rozó apenas la mejilla antes de perderse en el aire.
—¿Eso es todo? —preguntó Luis enderezándose lentamente, llevándose una mano a la mejilla.
Levantó los puños a la altura del rostro, adoptando una guardia perfecta mientras una sonrisa pícara se dibujaba en sus labios. Juan sabía que Luis llevaba meses esperando una excusa para medirse con cualquier idiota que se cruzara en su camino.
El García barbudo gruñó furioso y lanzó una combinación de golpes. Luis los esquivó con movimientos fluidos, balanceándose de un lado al otro, sus botas marcando un ritmo casi musical contra el empedrado.
—Vamos, grandote —lo provocó.
El García barbudo arremetió otra vez, esta vez con los puños cerrados como martillos. Luis se movió hacia la izquierda, después hacia la derecha, esquivando cada golpe mientras mantenía esa sonrisa burlona.
—No te canses —dijo Luis sin perder el aliento—. Apenas estamos empezando.
El barbudo lanzó un derechazo que habría tumbado a cualquier hombre, pero Luis se agachó en el momento exacto. El puño pasó por encima de su cabeza mientras él se incorporaba con un gancho perfecto al estómago del García.
El hombre se dobló del dolor, jadeando. Luis aprovechó para conectar otro golpe en la sien, calculado y limpio. El García se tambaleó hacia un lado.
La multitud gritaba y aplaudía. Las mujeres se tapaban los ojos, pero seguían mirando entre los dedos.
Juan notó cómo los otros tres García se movían nerviosamente, intercambiando miradas. El más joven había puesto la mano cerca de su cinturón. Juan ajustó su posición, listo para intervenir.
Luis siguió bailando alrededor de su oponente, esquivando golpes desesperados mientras conectaba sus propios puñetazos con precisión quirúrgica. Un gancho a las costillas, otro al mentón, después una combinación rápida que hizo retroceder al barbudo hasta la pared de una casa.
—¿Quieres que pare? —preguntó Luis, fingiendo preocupación—. Solo tienes que pedírmelo por favor.
El García escupió otra vez y se lanzó con toda su furia restante, cargando como un toro herido. Luis esperó hasta el último momento, se hizo a un lado y extendió la pierna. El gigante tropezó con la bota de Luis y su propio impulso lo mandó de cabeza contra el empedrado.
El golpe resonó como un saco de grano cayendo de una carreta. El barbudo quedó tendido, gimiendo y tratando de incorporarse sobre sus codos.
Luis se irguió lentamente, secándose el sudor de la frente con la manga de su chaqueta. La multitud estalló en vitores.
—¿Alguien más quiere bailar? —preguntó Luis jadeando, pero manteniendo esa sonrisa desafiante.
Fue entonces cuando el chasquido metálico del martillo de una pistola cortó el aire.
—Ya fue suficiente, cabrón.
El García más joven tenía su revólver apuntando directamente al pecho de Luis. Sus manos temblaban ligeramente, pero el cañón no se movía.
Luis alzó las manos lentamente, sin perder la sonrisa, pero ahora respirando pesadamente por el esfuerzo de la pelea.
El sonido de otra pistola siendo amartillada resonó desde el costado. Juan tenía su arma desenfundada, apuntando directamente a la cabeza del joven.
—No hagas una estupidez.
Los otros dos García se apresuraron a levantar al barbudo del suelo, quien balbuceaba palabras sin sentido, aturdido por el golpe contra el empedrado.
La tensión en el aire se cortó cuando el estruendo de varios caballos al galope se escuchó desde las afueras del pueblo. Un grupo de jinetes emergió bajo la luz de la luna, sus siluetas recortándose contra el cielo nocturno como sombras amenazantes.
Eran cuatro hombres montados en caballos oscuros, sus rostros ocultos bajo sombreros de ala ancha. No venían con la prisa desesperada de quienes corren a una pelea, sino con la determinación pausada de quienes llegan a terminar una. Sus caballos reducían la velocidad al unísono, como si hubieran ensayado esa entrada.
El que encabezaba la comitiva era un hombre mayor, de barba gris y sombrero negro. El patriarca de los García, Pedro, desmontó de su caballo con la pesadez de quien carga años de rencores. A su lado se apearon tres hombres más: rostros curtidos por el sol y marcados por cicatrices, con esa quietud peligrosa que solo tienen quienes han visto demasiada violencia. Sus manos descansaban cerca de sus pistolas, pero no las tocaban. No necesitaban hacerlo.
Los ojos de Pedro fueron directamente a Juan, ignorando por completo la multitud, las pistolas desenfundadas y hasta a su propio hijo tirado en el suelo.
—Juan Moreno —dijo con voz ronca, caminando lentamente hacia él—. Parece que tenemos un problema.
Juan mantuvo su pistola firme en la cabeza del joven García.
—Tu muchacho baja su arma primero, Pedro. Después hablamos.
Pedro observó la escena: su hijo barbudo sangrando en el suelo, el más joven temblando con el revólver en la mano y Juan inmóvil como una estatua.
—Baja esa pistola, Tomás —ordenó Pedro sin alzar la voz.
El chico titubeó antes de bajar el arma. Solo entonces Juan bajó la suya.
—Largo de aquí —ordenó Pedro a sus hijos—. Van a volver al rancho caminando por hacerme ver a los Moreno.
Pedro no se inmutó. Sus tres acompañantes permanecieron montados, observando en silencio.
Juan guardó su arma en la funda y se irguió. Pedro caminó hasta quedar a un par de metros de él, lo suficientemente cerca para que sus palabras no se perdieran en el murmullo de la gente.
—¿Puedes explicarme por qué tu hermano estaba golpeando a mis hijos?
—Tus hijos estaban golpeando a uno de mis muchachos —respondió Juan sin alterarse—. Luis hizo lo que cualquier hombre decente habría hecho.
—Ese muchacho se metió con la mujer de mi Nicolás. En mi familia, eso se paga.
—En mi pueblo, nadie golpea a un hombre entre cuatro —replicó Juan—. Y mucho menos por una mujer que ya no quiere saber nada de él.
Pedro escupió al suelo, cerca de las botas de Juan. Al parecer, era una tradición familiar.
—Tu pueblo… como si realmente fuera tuyo.
—Ya vas a empezar con tus cosas, Pedro. El presidente nos dejó a cargo. 
—No he dicho mi última palabra, Juan. Esta es mi casa. Mi familia estuvo aquí cien años antes que la tuya.
—Pues de nada les sirvieron —intervino Luis, recargándose despreocupadamente contra la pared—, porque igual los echaron a patadas.
Los ojos de Pedro se encendieron de furia.
—Tal vez si te meto una bala entre los dientes…
—Esta ya no es tu casa —interrumpió Juan con frialdad—. No lo ha sido por años y no te la regresaremos.
Pedro se alejó lentamente de Juan, pero antes de montarse en su caballo se detuvo y giró la cabeza.
—Disfruta tu reino mientras puedas, Juan. Los tronos no duran para siempre.
Montó su caballo y, antes de espolear, se dirigió a la multitud:
—La próxima vez que alguno de ustedes toque lo que es de los García, Juan tendrá que tocar esa estúpida guitarra en su funeral.
Con eso, espoleó su caballo y se perdió en la oscuridad, seguido por sus tres hombres. Sus hijos heridos caminaron tras ellos, tambaleándose en la noche.
La multitud permaneció en silencio hasta que el sonido de los cascos se desvaneció completamente en la distancia. Solo entonces comenzaron los murmullos nerviosos.
Juan se acercó a Felipe, que seguía en el suelo tratando de incorporarse. Le ofreció la mano.
—¿Puedes caminar, muchacho?
Felipe asintió, aunque le costó ponerse en pie. Tenía el labio partido y un ojo morado, pero nada que no sanara en unos días.
—Gracias, don Juan. A usted también, don Luis.
Luis se apartó de la pared y se sacudió el polvo de la chaqueta.
—No hay de qué, Felipe. Pero la próxima vez que te enamores, asegúrate de que no sea de la mujer de un García.
Algunas personas rieron, aliviando un poco la tensión. Fernanda se acercó a Felipe y lo tomó del brazo para ayudarlo a caminar.
—Lo voy a llevar a que mi madre le cure las heridas —dijo, evitando la mirada de los hermanos Moreno.
Juan notó la incomodidad de la chica, así que, siguiendo su instinto, preguntó:
—¿Ocultas algo, Fernanda?
La chica se tensó tras la pregunta, confirmando con su lenguaje corporal que sí que escondía algo.
—Está bien —dijo Felipe entre quejidos—. Es mejor decirles.
Fernanda se giró lentamente hasta que su mirada se encontró con los ojos de los Moreno.
—Felipe y yo… no estamos saliendo —dijo finalmente—. No sabía cómo quitarme a Nicolás de encima, así que le pedí a Felipe que me ayudara. No pensé que se lo tomaría tan a pecho.
—¿Es eso cierto, Felipe? —preguntó Juan con tranquilidad.
—Sí, señor. Lo siento si me puse en peligro… solo intentaba ayudar.
Luis se acercó hasta Felipe y le puso una mano en el hombro; su sonrisa se ensanchó.
—¡Qué hombre! —gritó Luis con genuina admiración—. ¡Este muchacho arriesgó el pellejo por defender a una dama!
El pueblo estalló en vítores. “¡Bravo, Felipe!”, gritó alguien desde atrás.
—¡Todos a acompañar al héroe! —declaró Luis—. —¡Vamos a llevarlo como se debe a casa de doña Carmen, y de ahí, vámonos a la cantina de José Luis que esta noche invita la casa Moreno!
Los hermanos Herrera y otros hombres jóvenes formaron un círculo protector alrededor de Felipe, ayudándolo a caminar mientras la multitud los siguió en procesión improvisada hacia la casa de Fernanda.
—Bueno, hermano, eso fue más emocionante que mi guitarra —dijo Juan, caminando junto a Luis.
—Sí, pero también más peligroso —respondió Luis—. Pedro no va a olvidar esto.
—Ve a la casa y cuéntale a madre lo que pasó. Te alcanzaré después.
Luis asintió y se dirigió hacia donde había dejado su caballo. Subió de un salto y, como un destello, avanzó por la calle principal en dirección a la hacienda Moreno.


Acto 1

Capítulo 1. Las tres fuerzas.
Ángel Moreno había subido a la torre de la iglesia con su libro, como cada sábado. Desde ahí podía escuchar la guitarra de Juan sin tener que bajar a saludar a la gente del pueblo.
Estaba perdido entre las páginas cuando el bullicio y la emoción se desvanecieron de golpe. La gente había dejado de bailar y su hermano había dejado de tocar.
Se asomó por el borde de piedra. Abajo, el sombrero de Juan se alejaba rápido, jalando a la gente como un imán. Ángel resopló. Seguro fue Luis. Siempre era Luis buscando quién se la pagara. 
—Par de animales —murmuró para sí mismo. 
Regresó a su rincón. Sus hermanos servían para los golpes; él servía para no estorbar. 
Abrió el libro de nuevo, intentando usar las letras como escudo contra el ruido de afuera.
Un par de minutos después, la tranquilidad de Ángel se vio interrumpida por un grito desde debajo de la iglesia. 
—¡Mano! 
Ángel cerró su libro y se quedó en silencio para confirmar lo que había escuchado. 
—¡Ángel! ¡Baja de ahí! 
—¿Qué pasa? —gritó Ángel hacia abajo.
—Los García están golpeando a un muchacho del pueblo. Juan fue a enfrentarlos, pero son varios contra él. ¿Vienes?
El nombre García cayó sobre Ángel como agua fría. Su padre les había contado historias. Hombres muertos, sangre en las calles. Pero sus manos temblaban solo de pensarlo. Luis y Juan nacieron para esto. Él no. Si iba, solo estorbaría. Solo sería otro problema que cuidar.
—No, hermano. Estoy algo ocupado aquí arriba.
—¿En serio, Ángel? —Luis alzó la voz con exasperación—. ¡Son los pinches García! Juan puede estar en problemas de verdad.
—Seguro que tú y Juan pueden arreglárselas.
Luis sacudió la cabeza con frustración y espoleó su caballo. 
—Está bien, quédate con tus libros. Pero si algo le pasa a Juan, no vengas a llorar después.
Con eso, tiró de las riendas bruscamente, haciendo que su caballo girara en una nube de polvo. El galope resonó contra el empedrado mientras se alejaba de la plaza, las espuelas tintineando con cada zancada del animal.
Ángel vio desaparecer a Luis entre las sombras de la noche y sintió un nudo en el estómago. Las palabras de su hermano resonaban en su cabeza.
Se quedó parado en el borde de la torre, con el libro olvidado en sus manos. Podía escuchar a lo lejos gritos y voces alteradas. Su corazón le decía que debía ir, que sus hermanos lo necesitaban, pero sus piernas no se movían.
“Solo los estorbaría”, murmuró para sí mismo, tratando de convencerse. Pero la excusa sonaba hueca incluso en sus propios oídos. Finalmente, con un suspiro resignado, se sentó de nuevo contra la pared de la torre y abrió su libro. 
Las páginas temblaron ligeramente en sus manos mientras trataba de concentrarse en la lectura.
Los minutos se arrastraron mientras Ángel fingía leer. Los gritos en la distancia se habían intensificado, y ahora podía escuchar el galope de más caballos. Las palabras en la página se difuminaban ante sus ojos; había leído la misma línea cinco veces sin comprenderla.
Cerró el libro con un suspiro frustrado. Si realmente había peligro con los García, su madre estaría sola en la hacienda. Luis y Juan podrían cuidarse solos, pero ella…
Se incorporó y guardó el libro bajo el brazo. Era hora de volver a casa.
Ángel bajó las escaleras de la torre y salió de la iglesia hacia la calle principal. Caminó despacio hacia casa, notando cómo las antorchas del portón principal parpadeaban en la brisa nocturna. Al cruzar el umbral familiar, el aroma de los naranjos del patio lo recibió como siempre, mezclándose con las flores de bugambilia que su madre cuidaba con tanto esmero.
El patio central estaba en silencio; solo se escuchaba el murmullo suave del agua en la fuente de cantera. 
Frente a él, el patio interior de la hacienda respiraba quietud. La fuente central murmuraba su canción nocturna. Cinco escalones de cantera rosa conducían al portal principal, donde los quinqués colgantes proyectaban círculos dorados sobre las puertas talladas. A cada lado se extendían las alas de la construcción: almacenes al oeste, establos al este.
Ángel subió los escalones hacia el portal, pero antes de entrar se detuvo. Volteó hacia la entrada principal, viéndola con culpa al pensar que había dejado solos a sus hermanos.
Una voz firme y cálida interrumpió sus pensamientos:
—Me han contado que tus hermanos andan en un pleito —dijo su madre desde la entrada de la casa, acomodándose el rebozo—. Luna vino corriendo a avisarme.
—Sí… algo así me dijo Luis —respondió Ángel, apenado.
Ella salió con calma y lo tomó del brazo. Juntos caminaron hasta quedar frente a la fuente del patio, contemplando el jardín nocturno en silencio.
—¿Te pidió que fueras con él?
—Sí, pero no sé por qué. Ellos pueden resolver cualquier cosa por sí mismos.
—No quería tu fuerza, hijo. Quería tu compañía.
Lo llevó a sentarse en el primer escalón del portal.
—Luis habló conmigo hace días. Me preguntó por qué no convives más con ellos. Cree que les huyes.
—¿De verdad? Apenas me notan, madre. No creo que sea eso.
Elena dejó escapar un suspiro suave.
—Tu hermana me escribió el mes pasado.
Ángel alzó la vista.
—¿Carolina?
—Dice que en el Hospital General de la Ciudad de México buscan administradores. Me pidió que te mandara con ella.
El corazón de Ángel dio un vuelco.
—¿Y qué le respondiste?
Elena hizo una pausa, midiendo sus palabras.
—Que esa decisión es tuya, no mía. Pero tiene razón en algo: leer libros no es poco. Tu padre leía la Biblia en voz alta para todos nosotros. Decía que las palabras tenían poder, que podían sanar tanto como los puños podían destruir.
Se acercó a él, colocando una mano sobre su hombro.
—Liderar no es solo dar órdenes ni pelear a golpes. Es también pensar, entender, hablar con justicia. Yo no crié ciegos, hijo. Tus hermanos saben que eres distinto. Y yo necesito ese don aquí.
Ángel alzó la vista, sorprendido.
—Tus hermanos te admiran más de lo que confiesan. Solo que no saben decirlo.
En la distancia, el sonido de cascos regresando al pueblo cortó la calma de la noche.
Luis apareció a galope tendido montado en su caballo blanco. Ángel no pudo evitar sonreír, admirando lo bien que se veía su hermano como jinete, incluso después de una pelea.
Luis bajó de un salto elegante y entregó las riendas a Aurelio, el mozo de cuadra. El caballo resoplaba por el galope. Luis se sacudió el polvo del camino y caminó con paso confiado hacia ellos. —Madre —dijo, quitándose el sombrero con una pequeña reverencia—. Hermanito.
Ella se puso de pie con esa mezcla de alivio y firmeza que le era natural. Tomó a Luis por los hombros y lo examinó con ojo atento.
—Tan guapo como siempre… pero con la camisa arrugada y la frente sucia. Eso no me gusta nada.
Luis sonrió con su confianza habitual.
—Estoy bien, madre. Solo fue un malentendido con los García.
—Los García no conocen de malentendidos —replicó ella, seca—. ¿Dónde está Juan?
—Se quedó en el pueblo, asegurándose de que Felipe llegue a su casa. Todo salió bien.
Ángel observaba en silencio, notando cómo Luis trataba de minimizar lo ocurrido.
—Cuéntame qué pasó exactamente —pidió ella, guiándolo a sentarse junto a Ángel—. Y no me escondas detalles, hijo.
Luis suspiró, resignado. 
—Los García estaban golpeando a Felipe. Cuatro contra uno. Juan intervino, pero… yo tuve que terminarlo.
—¿Hubo golpes?
—Solo yo golpeé —respondió con media sonrisa—. Al barbudo de Nicolás García. Le enseñé modales.
Ella lo miró fijo, sin reproche ni orgullo. 
—Luis, recuerda lo que siempre les he dicho: pelear para defender al débil es justo. Pero no confundan justicia con venganza o fanfarroneo.
Luis bajó la vista un instante, antes de continuar.
—Después llegó Pedro García con su gente. Hubo pistolas, madre.
Ángel sintió que el estómago se le encogía. Su madre palideció. 
—¿Pistolas? ¿Están bien?
—Todos estamos bien. Nadie disparó. Pero Pedro se fue muy enojado. Amenazó al pueblo entero.
Ella guardó silencio largo, hasta que su voz volvió serena: 
—Los García creen que la fuerza es gritar más fuerte. Nosotros sabemos que la fuerza es sostener la palabra.
—La frase de papá —reconoció Ángel con una sonrisa genuina.
Luis asintió con respeto. —Fernanda se llevó a Felipe con doña Carmen. Está bien.
—Iré a verlos mañana temprano.
Su madre se puso de pie con ayuda de Ángel, quien notó que sus manos temblaban ligeramente.
—Angelito, mañana a primera hora habla con don Andrés. Necesito una cita urgente con el presidente municipal. Esto no puede quedarse así.
Ángel asintió, mientras su madre entraba a la casa. Él y su hermano se quedaron en silencio mientras disfrutaban de la noche.
Unos minutos después, Ángel rompió el silencio:
—¿De verdad peleaste con cuatro de los García?
—¿Qué? No, claro que no —respondió Luis sonriendo—. Cuando quieres imponerte, solo debes concentrarte en el más fuerte y humillarlo para que el resto guarde sus distancias.
Ángel arqueó una ceja.
—Lo vas a exagerar, ¿cierto?
—Pues claro —Luis soltó una risa breve—. ¿De qué sirve ganar un pleito si no puedes contarlo como si fueras un héroe?
Se quedaron callados un instante, mirando el cielo oscuro y las estrellas que parecían escucharlos. Ángel, con voz más seria, rompió el silencio:
—Oye… pero ten cuidado, Luis. ¿Y si esta vez hubieran disparado de verdad?
—No cambiaría nada —contestó sin titubeos—. ¿Qué esperabas que hiciera? ¿Dejar que golpearan a Felipe delante de todos?
—No, claro que no —replicó Ángel, bajando la voz—. Solo digo que cada vez se arriesgan más, y tú… tú siempre vas de frente.
Luis se giró hacia él, con el rostro iluminado por la luz temblorosa de los quinqués. Había dejado de sonreír.
—Esta gente confía en nuestra familia para cuidarlos. No se trata de buscar pleitos, hermano, se trata de estar donde nos necesitan.
Un silencio breve volvió a caer entre los dos, hasta que Luis murmuró, casi con solemnidad:
—¿Recuerdas lo que siempre decía padre?
Ángel lo miró, y sin pensarlo respondió con la naturalidad de algo grabado en la sangre:
—Si la muerte toca las puertas en San Guzmán…
—Será un Moreno quien la reciba primero.
La frase quedó flotando en el aire frío. Luis le dio una palmada en el hombro, forzó una última sonrisa y montó de nuevo. Ángel lo vio perderse en la oscuridad del camino, sintiendo que la noche de repente se había vuelto más pesada, como si la frase de su padre hubiera invocado algo que ya no podían detener.

Capítulo 2. Un día en la hacienda.
Los gallos de la familia Moreno anunciaron el alba con su canto. El primer pregón rozó el sueño de Luis, pero solo al tercero consiguió arrancarlo de la cama. Como de costumbre, el olor a café de olla con canela recién hecho por su madre predominaba en toda la hacienda. Un olor tan exquisito que a veces instaba a Luis a probarlo, aunque sus últimos cinco intentos resultaran igual: muecas por el amargor y el recordatorio de su repudio por el café.
Con aletargamiento, Luis se puso uno de sus pantalones de trabajo y sus botas. Esta vez no eran sus botas blancas perfectamente boleadas, sino las gastadas y llenas de barro. Amaba verse bien, pero después de incontables regaños había comprendido que su apariencia no era prioridad en las labores matutinas.
Aunque habían pasado dos días desde su enfrentamiento con los García, Luis no lograba sacarse de la mente las amenazas de Pedro. Sabía que él estaría bien; siempre estaba bien. Pero el peso de tener que cuidar a todo San Guzmán poco a poco desgastaba sus hombros, acribillaba su espalda.
La camisa del día lo esperaba colgada detrás de la puerta de su habitación. Una camisa azul con bolsas en el pecho y finos grabados dorados que recorrían las mangas hasta el puño. Al descolgarla, leyó el bordado que su madre le había dejado por dentro del cuello:
“Siempre te amaré”
Su madre había confeccionado la ropa de trabajo de los tres hermanos, cada camisa hecha con amor, pensando en las necesidades de cada uno.
Luis le dio un beso al bordado y se la puso con cuidado, tratando de arrugarla lo menos posible.
Tomó un sombrero blanco de su repisa y salió por el pasillo principal de la hacienda, el aletargamiento completamente erradicado del cuerpo.
Recorrió el pasillo con su característico paso seguro, las espuelas tintineando suavemente contra el piso de baldosas. A través de las ventanas del corredor, la hacienda ya despertaba: los mozos abrían los establos, el humo se alzaba de las cocinas de las casas menores y las voces de sus tíos resonaban dando instrucciones para el día.
Bajó las escaleras principales sujetándose del pasamanos de hierro forjado, sintiendo el frescor de la cantera rosa bajo sus botas. Antes de girar hacia el comedor, Luis dio una respiración profunda y cambió su semblante por uno alegre. Al girar, lo recibió una imagen que con el tiempo había empezado a apreciar: la cocina estaba llena de vida.
El fogón de leña crepitaba en el centro, lanzando chispas naranjas que iluminaban las vigas de madera del techo. Ollas de barro borboteaban sobre el fuego, desprendiendo vapor que se enroscaba hacia las ventanas abiertas. Su madre se movía entre las llamas con la destreza de quien había pasado décadas en esa cocina, removiendo el atole con una mano mientras con la otra volteaba las tortillas en el comal.
Dos muchachas —Lupita y Rosa, hijas de don Esteban— servían platos humeantes de frijoles refritos y huevos rancheros a los trabajadores que ya llenaban la larga mesa de madera. Eran casi quince hombres sentados en los bancos, algunos todavía tallándose los ojos, otros ya despiertos y conversando en voz baja mientras el café circulaba de mano en mano.
El aroma de las tortillas recién hechas se mezclaba con el del cilantro picado, la cebolla asada y el chile tatemado. En un rincón, las canastas de pan dulce esperaban junto a los jarros de atole de guayaba. Todo estaba dispuesto con ese orden natural que solo las manos de su madre sabían imponer.
La cocina era el corazón de la hacienda Moreno, y cada mañana latía así: cálida, ruidosa, viva.
Cuando notaron su presencia, uno a uno los trabajadores de la hacienda Moreno fueron saludando a Luis con un leve asentimiento. Por su parte, Luis se encargó de que todas las personas en la sala recibieran sus buenos días.
Con destreza esquivó todo el ajetreo del comedor hasta llegar con su madre. Ella lo vio acercarse y, sin interrumpir el ritmo de sus manos sobre el comal, le dedicó una sonrisa cálida.
—Buenos días, madre —dijo Luis, inclinándose para besarle la frente.
—Buenos días, hijo. Dormiste poco, ¿verdad? —respondió doña Elena, señalando con la barbilla las ojeras apenas visibles bajo sus ojos.
Luis soltó una risa breve.
—Lo suficiente.
Sin esperar respuesta, su madre le entregó su desayuno del día: unos huevos estrellados con frijoles refritos y un par de quesadillas humeantes, todo servido en un plato de barro tibio.
—Gracias, madre.
Luis giró hacia la mesa. Al pasar junto a Lupita, le dedicó un gesto amable.
—Buenos días, Lupita.
La muchacha levantó la vista brevemente, sus mejillas enrojeciendo de inmediato. Balbuceó algo ininteligible, bajó la mirada y apretó el paso hacia la cocina con la jarra de atole temblando ligeramente en sus manos.
Luis arqueó una ceja, desconcertado, pero no le dio mayor importancia. Se dirigió a la mesa larga de madera y tomó asiento entre los trabajadores, dejando el plato frente a él con un golpe suave.
Partió una quesadilla con los dedos y la llevó a la boca, sintiendo el queso derretirse en su lengua. A su alrededor, las conversaciones de los trabajadores fluían con naturalidad: planes para reparar la cerca norte, quejas sobre una yegua terca que no dejaba herrarla, chistes viejos que arrancaban risas nuevas.
—Don Luis —dijo Aurelio, partiendo un pan dulce—. Mi hijo dice que anoche hubo baile con los García.
El ruido de los cubiertos cesó de golpe. Quince pares de ojos se clavaron en Luis. Él masticó con una calma estudiada, sabiendo que esos hombres no querían la verdad sucia de la calle; querían una leyenda.
—Digamos que a Nicolás García le hizo falta aprender a caer —dijo Luis, y soltó una risa corta.
La promesa de otra historia épica hizo que toda la sala posara sus ojos sobre él.
Se puso de pie y, durante los siguientes minutos, transformó la trifulca callejera en una epopeya. Caminaba alrededor de la mesa imitando los golpes, pero mejorados. Omitió el miedo que sintió, omitió que Juan tuvo que salvarlo con la pistola y convirtió sus esquivas desesperadas en pasos de baile.
—…y cuando vi que se levantaba —narró, haciendo un gesto teatral que hizo brillar sus anillos bajo la luz de la cocina—, le dije: “Quédate abajo, grandulón, el suelo te quiere más que ella”.
Las carcajadas estallaron en la cocina. Los peones vitoreaban, devorando la mentira porque la realidad de los García les daba demasiado miedo.
Luis volvió a sentarse. Por un segundo, al rozarse las costillas magulladas, hizo una mueca de dolor que nadie vio. Había ganado el aplauso, pero la amenaza de Pedro García seguía allá afuera, real y furiosa. 
Luis dejó que las risas se apagaran solas, su rostro perdiendo poco a poco la sonrisa teatral hasta quedar serio. 
—Pero no se confíen —cortó de repente, bajando la voz—. Si ven una sombra que no reconozcan, me avisan. A mí o a Juan.
Los trabajadores terminaron su desayuno en un silencio más apagado. Uno a uno fueron dejando sus platos vacíos sobre la mesa, limpiándose las manos en sus pantalones de manta antes de ponerse de pie. Aurelio fue el primero en levantarse, seguido por los demás.
—Vamos, muchachos —dijo, ajustándose el sombrero—. El maíz no se va a cosechar solo.
Luis se incorporó también, dejando su plato a medio terminar. Su madre apareció a su lado sin que él la escuchara acercarse, como siempre hacía.
—Ten cuidado hoy —le dijo en voz baja, tocándole el brazo con suavidad.
—Siempre tengo cuidado, madre.
Ella lo miró con esos ojos que parecían ver más allá de las palabras.
—Sabes a qué me refiero.
Luis asintió y le dio un beso en la mejilla antes de seguir a los trabajadores hacia la salida.
El grupo atravesó el patio central de la hacienda en silencio, sus botas resonando contra las piedras del empedrado. Las sombras de la madrugada todavía se aferraban a los rincones, pero el cielo al oriente ya comenzaba a teñirse de naranja y rosa.
Al cruzar el portón principal, el aire fresco de la mañana los recibió como una bofetada suave. Luis respiró hondo, llenándose los pulmones con el olor a tierra húmeda y hierba recién cortada. El rocío todavía brillaba sobre las hojas de los naranjos que flanqueaban el camino.
Los primeros rayos del sol se asomaban por detrás de las montañas distantes, proyectando líneas doradas que cortaban la bruma matinal. La luz tocó primero las copas de los árboles, después los techos de las casas del pueblo a lo lejos, y finalmente comenzó a descender sobre los campos de maíz que se extendían como un mar verde hasta donde alcanzaba la vista.
—Va a hacer calor hoy —comentó Aurelio, entornando los ojos hacia el horizonte.
—Como siempre —respondió Luis, ajustándose el sombrero para protegerse del sol que ya empezaba a calentar.
Se detuvo y alzó la voz para que todos lo escucharan.
—Muchachos, acérquense con Aurelio. Él les dirá qué necesitamos hoy.
Aurelio asintió con una mezcla de orgullo y responsabilidad, y los hombres se agruparon a su alrededor mientras él comenzaba a repartir las tareas del día: quiénes irían a los campos de maíz, quiénes repararían la cerca norte, quiénes se encargarían del ganado.
Luis se apartó del grupo, dejando que Aurelio tomara el mando. No era necesario que estuviera ahí parado dando órdenes que otros podían dar mejor que él. Su padre le había enseñado eso: un buen patrón sabe cuándo hablar y cuándo dejar que sus hombres trabajen.
Se quedó parado un momento en el camino, observando cómo el pueblo de San Guzmán despertaba a lo lejos. El humo de las primeras cocinas se alzaba perezoso hacia el cielo, y el tañido de las campanas de la iglesia anunciaba la misa de la mañana.
Todo parecía tranquilo. Demasiado tranquilo.
Luis sacudió la cabeza, apartando los pensamientos oscuros, y se dirigió hacia los establos. Había trabajo que hacer, y los García tendrían que esperar.
A lo lejos, más allá de donde terminaban los cultivos, Luis alcanzó a distinguir la cuadrilla de Juan. Ya llevaban horas trabajando —habrían comenzado antes del amanecer— y, sin embargo, sus movimientos seguían siendo precisos, coordinados, como los de una máquina bien aceitada.
No había gritos ni empujones. Solo el ritmo constante de las hoces cortando el maíz y las voces tranquilas dando indicaciones. Juan estaba en medio de todos, trabajando hombro con hombro con sus hombres, sin distinciones.
Luis sonrió con una mezcla de admiración y envidia sana. Para los trabajadores era un honor estar en la cuadrilla de Juan. No por miedo ni por obligación, sino porque Juan nunca les pedía algo que él mismo no estuviera dispuesto a hacer primero. Por eso sus hombres llegaban a las cuatro de la mañana con la energía de quien va a una fiesta, no a una jornada de trabajo.
Eran el reflejo perfecto de su líder: disciplinados, leales, inquebrantables.
Luis volvió la vista hacia los establos. Su cuadrilla era distinta —más ruidosa, más alegre—, pero igual de efectiva. Cada hermano Moreno tenía su forma de liderar, y ambas funcionaban.
Luis pensó en Ángel. A estas horas ya estaría despierto, probablemente desayunando con el padre Matías y ayudando en la sacristía. O tal vez revisando los números de la cantina de José Luis, como había mencionado el sábado. Ángel no tenía cuadrilla propia, no comandaba hombres en los campos ni se paseaba a caballo dando órdenes.
Pero Luis había visto cómo la gente del pueblo lo buscaba cuando necesitaban que alguien les leyera una carta, les ayudara con las cuentas o simplemente les escuchara sin juzgar. Ángel lideraba con la pluma y la palabra, no con la pistola ni el puño. Y aunque él mismo no lo supiera, los trabajadores también encontraban paz bajo su tranquilidad.
Tres hermanos. Tres formas de cuidar a San Guzmán.
En el establo, Elegante dominaba sobre todo lo demás. Sebastián, el segundo al mando detrás de Aurelio, lo estaba cepillando con delicadeza. El caballo blanco se meneaba con felicidad tras cada pasada del cepillo, sus crines plateadas brillando incluso bajo la luz tenue del establo.
—Buenos días, Sebastián —saludó Luis, acercándose con paso tranquilo.
—Buenos días, don Luis —respondió el hombre sin dejar de cepillar—. Elegante ya estaba inquieto. Creo que sabía que usted vendría.
Luis sonrió y extendió la mano para acariciar el cuello del animal. Elegante giró la cabeza hacia él, resoplando suavemente como saludo.
—Claro que sabía. Este caballo me conoce mejor que yo mismo.
Sebastián soltó una risa breve mientras le entregaba el cepillo a Luis.
—Ayer lo noté más nervioso de lo normal. ¿Pasó algo?
Luis tomó el cepillo y comenzó a pasarlo por el lomo de Elegante con movimientos largos y seguros. El caballo se calmó al instante bajo el toque familiar de su dueño.
—Digamos que tuvimos un encuentro con los García el sábado.
Sebastián se tensó ligeramente.
—Ya me lo imaginaba. Aurelio me contó algo esta mañana.
—Sabes, a veces pienso que Elegante es capaz de leer mis pensamientos; creo que imita mi sentir o algo así.
Sebastián lo miró con extrañeza.
—O tal vez me estoy volviendo loco.
—Don Aurelio dice que los caballos son más inteligentes de lo que creemos, así que no descarto nada.
Luis se paró un tiempo a procesar su comentario. Finalmente, cortó la conversación.
—Ve con Aurelio. Seguro ya te está buscando para repartir el trabajo.
Sebastián asintió y salió del establo con paso rápido, dejando a Luis a solas con Elegante.
Luis se quedó ahí un momento, recargado contra el flanco cálido de su caballo, escuchando los sonidos matutinos de la hacienda: el mugido lejano del ganado, el canto de los gallos que se negaban a callarse, las voces de los hombres organizándose para el día.
—Nos espera un día largo, amigo —murmuró al oído de Elegante—. Pero ya hemos tenido peores.
El caballo resopló como si estuviera de acuerdo.
Luis se enderezó y miró hacia los campos donde la cuadrilla de Juan seguía trabajando con ese ritmo implacable.
—Será mejor que vayamos a ver cómo va todo con Juan —dijo, más para sí mismo que para el caballo.
Tomó la silla de montar que descansaba sobre la cerca del establo y la colocó sobre el lomo de Elegante con movimientos practicados mil veces. El caballo se mantuvo quieto, paciente, mientras Luis ajustaba las correas y aseguraba los estribos.
—Listo —murmuró, dándole una palmada en el cuello.
Montó con un movimiento fluido, acomodándose en la silla mientras tomaba las riendas. Elegante pateó el suelo con impaciencia, listo para correr.
—Tranquilo —dijo Luis con una sonrisa—. Ya vamos.
Espoleó suavemente al caballo y salió del establo al trote. El sol de la mañana ya pegaba con fuerza, calentando el aire y haciendo brillar el rocío que aún se aferraba a las plantas. A su alrededor, los trabajadores de su cuadrilla ya estaban dispersos: unos reparaban la cerca norte, otros guiaban el ganado hacia los pastos frescos, algunos más cargaban sacos de grano hacia los almacenes.
Luis los saludó con un gesto al pasar, y ellos respondieron quitándose el sombrero o levantando la mano.
Una vez fuera del perímetro inmediato de la hacienda, Luis le dio rienda suelta a Elegante. El caballo no necesitó más invitación. Salió disparado como una flecha blanca, sus cascos golpeando la tierra con un ritmo constante que resonaba en el pecho de Luis.
El viento golpeó su rostro, despeinándolo por completo a pesar de su sombrero bien ajustado. Luis sonrió. Esta era su parte favorita del día: la velocidad, la libertad, aunque fuera por unos minutos.
Los campos pasaban a ambos lados, la tierra todavía agrietada por las sequías recientes. A lo lejos, la cuadrilla de Juan se hacía más visible con cada segundo: un grupo de hombres moviéndose con precisión entre las hileras, trabajando la tierra seca con picos y palas, preparando el terreno para la próxima siembra con la esperanza de que las lluvias finalmente llegaran.
Luis redujo la velocidad cuando se acercó, haciendo que Elegante pasara del galope al trote y finalmente al paso. No quería llegar levantando polvo sobre los trabajadores.
Juan estaba exactamente donde Luis esperaba encontrarlo: en medio de sus hombres, con la camisa arremangada hasta los codos y el sombrero empujado hacia atrás, hundiendo una pala en la tierra agrietada con la misma eficiencia que cualquiera de ellos. Su rostro brillaba de sudor, pero sus movimientos eran constantes, sin prisa, pero sin pausa.
Uno de los trabajadores lo vio llegar primero y le dio un codazo a Juan, señalando hacia Luis. Juan se enderezó, limpiándose la frente con el dorso de la mano, y esperó a que su hermano se acercara.
Luis desmontó antes de que Elegante se detuviera por completo, aterrizando con un golpe suave sobre la tierra.
—Buenos días, hermano —saludó con una sonrisa.
Juan asintió, apoyando su pala contra el hombro.
—Buenos días. ¿Todo bien en la hacienda?
—Todo tranquilo. Vine a ver cómo iban las cosas por acá.
Juan lo miró con esa expresión que Luis conocía bien: la que decía “sé que no viniste solo a supervisar”.
—¿O viniste porque no puedes quedarte quieto pensando en los García?
Luis soltó una risa breve.
—¿Cómo lo sabes? No le he contado a nadie que…
—Te conozco. Tu paseo nocturno de anoche no es normal en ti.
Luis se quedó extrañado. Se había asegurado de que nadie lo viera. Por un momento había olvidado que Juan tenía todo el pueblo controlado. Era obvio que se enteraría si su hermano decidía dar un paseo para despejar la mente a medianoche.
Suspiró.
—Tengo un mal presentimiento, Juan. Pedro no es famoso por dejar las cosas así.
—Lo sé —respondió Juan, limpiándose el sudor del cuello con un pañuelo—. Por eso madre y yo tenemos una cita con Pedro y el presidente municipal esta tarde.
—¿De verdad? —Luis se enderezó, interesado—. ¿Puedo ir con ustedes?
—No. Tú te vas a quedar a cuidar San Guzmán.
La respuesta llegó tan rápida, tan definitiva, que Luis sintió un pellizco en el pecho. Asintió lentamente, aunque algo en su interior comenzaba a removerse.
—¿Y Ángel? Podría ayudarte con la diplomacia. Sabes que tiene don para las palabras.
—Lo pensé —admitió Juan, como si ya hubiera considerado y descartado todas las posibilidades sin consultarle a nadie—. Pero temo que Pedro se le meta en la cabeza. Todavía no está listo para ese tipo de presión.
El calor del sol parecía más intenso de repente. Luis sintió cómo sus manos se cerraban ligeramente alrededor de las riendas de Elegante.
—Ya no es un niño, Juan. Claro que puede con esto.
Juan clavó su pala en el suelo con fuerza y recargó su peso sobre ella. Su mirada se volvió más seria, más inamovible.
—Ángel piensa demasiado las cosas. Y con Pedro García, si piensas, te mueres. Todavía no está listo. ¿Entendiste?
Luis apretó la mandíbula. La palabra “Entendiste” resonó en su cabeza como una orden militar, no como una conversación entre hermanos. Algo dentro de él, que había estado acumulándose desde la primera negativa, finalmente se desbordó.
—No soy uno de tus peones, Juan. No me hables así.
Juan levantó la vista, sorprendido por el cambio en la voz de su hermano.
—No dije que lo fueras.
—Pero así me hablas —respondió Luis, bajándose de Elegante para quedar a la altura de Juan—. “Tú te vas a quedar a cuidar San Guzmán. Entendido.” Como si no tuviera opinión en esto.
Juan se enderezó completamente, limpiándose las manos en el pantalón.
—Luis, no es momento para…
—¿Para qué? —¿Para qué te diga lo que pienso? —Luis se quitó el sombrero y se pasó la mano por el cabello con frustración—. Tú decides quién va, quién se queda, quién está listo y quién no. Siempre decides tú.
—Alguien tiene que hacerlo —replicó Juan con calma, esa calma que solo hacía enojar más a Luis. —Padre me dejó a cargo, ¿Recuerdas?
—Sí, pero no siempre tiene que ser de esa manera. Ángel tampoco es un niño que necesite tu aprobación para todo. Y yo… —Se detuvo, respirando hondo—. Yo también puedo pensar, Juan. También puedo decidir.
Juan lo observó en silencio por un momento largo. Los trabajadores cercanos habían dejado de cavar, sintiendo la tensión entre los hermanos, pero sin atreverse a intervenir.
—¿Terminaste? —preguntó Juan finalmente, sin alterarse.
Luis apretó los puños a los costados, pero asintió.
—Terminé.
Juan dio un paso hacia él, bajando la voz para que solo Luis pudiera escucharlo.
—Tienes razón. A veces olvido que no todos necesitan que les diga qué hacer. —hizo una pausa—. Pero alguien tiene que mantener el orden en esta familia, Luis. Y si no soy yo, ¿quién será? El peso de esta carga me está rompiendo; no quiero lo mismo para ti.
Luis sostuvo la mirada de su hermano, sintiendo cómo la rabia se mezclaba con algo más complicado: entendimiento, frustración, resignación.
—No te pido que dejes de liderar, Juan. Solo… pregunta de vez en cuando. En lugar de ordenar.
Juan asintió lentamente, como si estuviera procesando las palabras.
—Está bien. Te lo pregunto entonces: ¿Crees que deberíamos llevar a Ángel con nosotros a la reunión con Pedro García?
Luis se quedó callado un momento, sorprendido por el cambio. Miró hacia el pueblo a lo lejos, pensando en su hermano menor.
—No —admitió finalmente—. Todavía no. Pero no porque no sea capaz, sino porque Pedro lo usaría para presionarnos. Y Ángel no necesita cargar con eso todavía.
Juan dejó escapar un suspiro que parecía llevar años de peso.
—Entonces estamos de acuerdo.
—Sí —respondió Luis, poniéndose el sombrero de nuevo—. Pero la próxima vez, empieza con una pregunta en lugar de una orden. Funciona mejor conmigo.
Una pequeña sonrisa apareció en el rostro de Juan, apenas visible bajo su sombrero.
—Lo intentaré.
Luis montó a Elegante de nuevo, ajustándose en la silla.
—¿Necesitas algo antes de tu reunión?
—Que mantengas el pueblo tranquilo. Si Pedro manda a alguien a provocar, no muerdas el anzuelo.
Luis sonrió con ironía.
—¿Eso es una orden o una pregunta?
Juan lo miró con esa expresión entre seria y divertida que solo él podía hacer.
—Es un ruego de tu hermano mayor.
—Así está mejor —respondió Luis, tirando suavemente de las riendas—. Ten cuidado con el viejo García, Juan. No confío en él.
—Yo tampoco. Por eso madre va conmigo.
Luis asintió y espoleó a Elegante, alejándose al trote mientras Juan volvía a tomar su pala.
Los trabajadores reanudaron su labor en silencio, pero más de uno había visto el intercambio entre los hermanos Moreno.

Capítulo 3. Un peso heredado.
Juan entró a su habitación con los pies adoloridos de cansancio. No era un cansancio pesado o abrumador, sino ese dulce agotamiento del cuerpo tras completar una jornada de trabajo honesto. Se quitó las botas con calma, dejando caer los restos de tierra sobre las baldosas del piso como tributo al día cumplido.
La camisa húmeda de sudor siguió, revelando los hombros marcados por años de labor bajo el sol. Los pantalones de trabajo cayeron después, igual de empapados.
Se tendió en su cama, mirando las vigas de madera del techo que su padre había tallado con sus propias manos. Desde su muerte, estos momentos de quietud se habían vuelto raros en la vida de Juan. Recordó el día del entierro de su padre. Quince años. Todavía sentía la tierra fresca bajo sus manos cuando ayudó a echar las primeras paladas sobre el ataúd.
A pesar del cansancio, del dolor en el cuerpo, del peso en la mente, Juan jamás renegó de sus responsabilidades. No porque no tuviera otra opción, sino porque había hecho una promesa junto al lecho de muerte de su padre. Una promesa que no era carga, sino privilegio. El privilegio de continuar el legado Moreno, de proteger lo que generaciones antes habían construido con sangre y sudor.
Su padre le había confiado todo. Y Juan lo llevaría con orgullo hasta su último aliento.
Se incorporó con un suspiro y caminó hacia el rincón de su habitación donde descansaba la tina de zinc. No era una bañera elegante como las que había en las casas de la ciudad, pero cumplía su función. Junto a ella, dos cubetas de agua que Rosa había dejado calentando al sol durante la tarde.
Juan vertió el agua sobre su cabeza, sintiendo cómo el líquido tibio arrastraba el polvo y el sudor del día. Cerró los ojos mientras el agua corría por su rostro, su cuello, su pecho. En estos momentos de soledad, cuando nadie lo miraba esperando órdenes o decisiones, Juan se permitía el lujo de pensar.
San Guzmán.
El nombre resonaba en su mente como una oración. Trescientos almas bajo su cuidado. Veintiún familias que dormían tranquilas porque confiaban en que los Moreno las protegerían. Esa confianza era más pesada que cualquier costal de maíz, más afilada que cualquier azadón.
Pedro García sabía exactamente dónde atacar. No había amenazado directamente a los hermanos Moreno. No, el viejo era más astuto que eso. Había amenazado al pueblo entero. “Juan tendrá que tocar su guitarra en el funeral”, había dicho. Como si los muertos fueran responsabilidad exclusiva de Juan. Como si cada vida perdida fuera una nota desafinada en su canción.
Y quizás lo era.
Juan tomó el jabón de sebo y comenzó a frotarlo contra su piel, mecánicamente, mientras su mente trabajaba en la reunión de la tarde. El presidente municipal estaría ahí, don Rodrigo Salinas, un hombre político que se inclinaba hacia donde soplaba el viento más fuerte. No era un aliado confiable, pero tampoco un enemigo declarado. Era, simplemente, un hombre que quería mantener la paz para conservar su puesto.
¿Qué querría Pedro en esa reunión? No vendría solo a quejarse. Los García no operaban así. Vendrían con exigencias. Tal vez pidieran que los Moreno pagaran por las heridas de Nicolás. Tal vez exigieran que Felipe fuera castigado públicamente por “ofender” a su familia. O peor aún, tal vez pedirían algo que Juan no podría darles sin traicionar al pueblo.
El agua seguía cayendo, ahora más fría. Juan se enjuagó el jabón con movimientos precisos.
Su madre iría con él. Eso era bueno. Ella tenía una forma de hablar que desarmaba incluso a los hombres más tercos. No con suavidad ni con ruegos, sino con esa autoridad tranquila que solo las mujeres fuertes poseían. Pedro García podía ser muchas cosas, pero era un hombre de su generación: no faltaría al respeto a una viuda en público.
Pero Juan sabía que la diplomacia tenía sus límites. Si Pedro pedía sangre, ninguna palabra bonita lo detendría. Y si pedía tierra, ningún acuerdo verbal valdría más que la codicia.
Juan salió de la tina y se secó con una toalla áspera. El agua sucia formaba un charco a sus pies, oscura con la tierra del día.
Caminó hacia su armario y sacó el traje de charro negro. No era el de trabajo ni el de las fiestas; era el que su padre había usado para negociar con hacendados, para representar a San Guzmán ante las autoridades estatales, para recordarles a todos que los Moreno no eran simples campesinos.
Se vistió con meticulosa reverencia, ajustándose cada botón, cada hebilla.
Se miró frente al espejo de cuerpo entero. El traje aún le quedaba grande: las mangas colgaban un par de centímetros más allá de sus muñecas, y los hombros marcaban el espacio ancho y definido que había llenado la espalda de su padre. Nadie más podía notarlo, pero Juan lo veía. Veintiséis años, pero su rostro ya mostraba las líneas de un hombre que había envejecido rápido, no por los años, sino por las decisiones.
¿Cuántas decisiones más tendría que tomar antes de que todo esto terminara? ¿Cuándo podría simplemente ser Juan, y no el líder de los Moreno? ¿Cuándo podría tocar su guitarra sin que cada nota cargara el peso de trescientas vidas?
Tal vez nunca.
Tal vez eso era exactamente lo que significaba ser un Moreno.
Descansando en la cintura, bajo la tela del traje, Juan llevaba su pistola. La desenfundó con un movimiento lento y la dejó sobre la cama. Este enfrentamiento tendría que hacerlo únicamente con la voz y con la razón. No con el plomo.
Se ajustó el sombrero negro y salió de su habitación. Su madre lo estaría esperando. Y después de ella, Pedro García y Don Rodrigo Salinas.
Que viniera lo que tuviera que venir.
Juan Moreno estaba listo.

Bajó por las escaleras que conducían directamente a la puerta principal del casón. Ángel lo esperaba recargado en el marco, con los brazos cruzados sosteniendo varios libros contra el pecho.
—Hermano, me enteré de tu reunión —dijo Ángel, enderezándose—. Me tomé el tiempo para buscar algo que pudiera ayudarte.
Abrió uno de los libros y señaló una página llena de números y anotaciones.
—Si Pedro empieza a ponerse quisquilloso con la ley o con el honor, recuérdale que les debe al pueblo miles de pesos en impuestos atrasados. Mira —dijo, acercando el libro para que Juan pudiera ver las columnas de cifras—. Tres años sin pagar. Don Rodrigo no podrá ignorar eso.
Juan estudió los números brevemente, aunque su mente ya estaba procesando las implicaciones.
—Buen trabajo, Ángel.
—Pero ten cuidado —continuó su hermano menor, cerrando el libro con un golpe suave—. Ganar con números y leyes solo lo enfurecerá más. Podría convertir esto en algo mucho peor que impuestos y palabras.
Juan puso una mano sobre el hombro de Ángel, apretando ligeramente. Entendía el riesgo perfectamente: humillar a Pedro García con hechos lo volvería más peligroso, más impredecible. El orgullo herido siempre buscaba venganza.
—Lo sé —dijo Juan con voz firme—. Pero si vamos a perder, que sea porque peleamos con todo lo que teníamos. No, porque nos quedamos callados.
Una sonrisa pequeña apareció en el rostro de Ángel, quien asintió y se hizo a un lado, dejando pasar a su hermano mayor.
Juan cruzó el umbral y el sol de la tarde lo recibió como una bofetada cálida. La camioneta de la familia Moreno lo esperaba frente a la fuente del patio principal, su carrocería verde olivo brillando bajo la luz. Su madre ya estaba sentada en el asiento del copiloto, vestida de negro como siempre desde la muerte de su esposo, envuelta en un rebozo oscuro que no ocultaba la firmeza de su postura.
Juan rodeó la camioneta y subió. Al girar la llave, el motor tosió antes de rugir con vida, su ruido apagando por un instante el canto de los pájaros y las voces lejanas del pueblo.
—¿Todo listo, hijo? —preguntó su madre sin mirarlo, con la vista fija al frente.
—Todo listo, madre.
—No caigas en los juegos de Pedro, hijo —dijo ella, ajustándose el rebozo con un movimiento preciso—. Ese hombre ha peleado toda su vida. Tiene la lengua tan afilada como yo mis cuchillos. Serenidad y tranquilidad, mi niño.
—Sí, madre.
Juan puso la camioneta en marcha y salió por el portón principal de la hacienda. El camino de tierra lo llevaba directo hacia el pueblo vecino de Santa Rita, donde estaba la sede de la presidencia municipal. No pudo disimular su incomodidad; hubiese preferido montar a caballo, pero la comodidad de su madre era prioridad. Además, eran contadas las ocasiones en que usaban la camioneta Ford que les habían regalado hacía dos años.
La camioneta avanzó por el camino polvoriento, dejando atrás los campos agrietados de San Guzmán. A través del espejo retrovisor, Juan vio cómo la hacienda se hacía más pequeña con cada metro recorrido.
Su madre rompió el silencio:
—Tu padre también tuvo que enfrentarse a Pedro una vez. Fue hace muchos años, antes de que tú nacieras.
Juan la miró de reojo sin apartar mucho la vista del camino.
—¿Qué pasó?
—Tu padre ganó —respondió ella con una sonrisa apenas visible—. Pero no con amenazas ni con pistolas. Ganó porque Pedro se dio cuenta de que había más que perder peleando que negociando.
—¿Y crees que Pedro todavía piensa así?
Su madre guardó silencio un momento largo antes de responder.
—Creo que Pedro es un hombre viejo que ve cómo su tiempo se le escapa. Y los hombres viejos son los más peligrosos, porque ya no tienen nada que perder.
Juan asintió, procesando las palabras mientras el pueblo de Santa Rita aparecía en el horizonte: un conjunto de casas de adobe agrupadas alrededor de una plaza central, con la iglesia de cantera rosa dominando el paisaje y, junto a ella, el edificio de la presidencia municipal con su bandera tricolor ondeando perezosamente en la brisa.
Estacionó la camioneta frente al edificio. Antes de bajar, su madre lo detuvo con una mano sobre su brazo.
—Juan, escúchame bien —dijo, mirándolo directamente a los ojos—. Pase lo que pase ahí adentro, recuerda que no estás solo. Yo estaré a tu lado. Tus hermanos estarán esperándote en casa. Y San Guzmán entero confía en ti.
—Gracias, madre.
—No me agradezcas. Solo hazme sentir orgullosa de ti, como siempre lo haces.
Bajaron de la camioneta. Juan rodeó el vehículo y le ofreció su brazo a su madre, quien lo tomó con la dignidad de una reina.
Juntos subieron los cinco escalones de cantera que conducían a la puerta de la presidencia municipal.
Pedro García los estaría esperando adentro.
Juan respiró hondo, ajustó su sombrero y empujó la puerta.
El edificio de gobierno en Santa Rita era lo que se podría esperar de un municipio que fingía importancia sin tenerla realmente. La fachada de cantera rosa intentaba imitar la grandeza de los edificios coloniales de la capital, pero las grietas en las columnas y la pintura descascarada revelaban años de negligencia.
El interior no era mejor. Un pasillo estrecho de baldosas desiguales conducía a la oficina principal, flanqueado por paredes de adobe blanqueado donde colgaban retratos descoloridos de presidentes municipales olvidados. El techo de vigas oscuras dejaba caer telarañas que se mecían con la brisa que entraba por las ventanas sin vidrio.
El olor a tabaco rancio y papel viejo impregnaba el aire. A la derecha, un escritorio desvencijado servía de recepción, pero estaba vacío. La secretaria seguramente había sido despachada para esta reunión.
Juan y su madre avanzaron por el pasillo. Sus pasos resonaban contra las baldosas, anunciando su llegada. Al final del corredor, una puerta de madera tallada, que era la única cosa de valor en todo el edificio, permanecía entreabierta. A través de la rendija se filtraba luz amarillenta de un quinqué y el murmullo de voces masculinas.
Juan se detuvo frente a la puerta, sintiendo la mano de su madre apretando suavemente su brazo. Ella no dijo nada, pero su presencia le recordó quién era y por qué estaba ahí.
Empujó la puerta completamente.
La oficina del presidente municipal era apenas más grande que un cuarto de servicio. Un escritorio de caoba oscura dominaba el espacio, cubierto de papeles amarillentos y tinteros secos. Detrás de él, Don Rodrigo Salinas se puso de pie con una sonrisa nerviosa, su bigotillo sudoroso brillando bajo la luz del quinqué.
Pero no fue él quien captó la atención de Juan.
Pedro García estaba sentado en una de las dos sillas frente al escritorio, con una pierna cruzada sobre la otra y un puro humeante entre los dedos. No se levantó. No hizo ademán de saludar. Solo miró a Juan con esos ojos grises que habían visto demasiadas peleas y demasiados muertos.
A su lado, en la otra silla, estaba uno de sus hombres: un tipo joven de mandíbula cuadrada y cicatriz que le cruzaba la ceja. Tenía las manos sobre los muslos, quietas, pero sus ojos seguían cada movimiento de Juan como un perro guardián.
Don Rodrigo carraspeó incómodo.
—Don Juan, doña Elena —dijo con voz demasiado alta, demasiado alegre—. Pasen, pasen, por favor. Les agradezco mucho que hayan venido.
Juan entró sin prisa. El humo del puro de Pedro flotaba en el aire, espeso, amargo. Acercó una silla desde el rincón y ayudó a su madre a sentarse. Solo entonces se quitó el sombrero y permaneció de pie detrás de ella, con las manos descansando sobre el respaldo.
Pedro exhaló otra bocanada de humo.
—Qué considerado, Juanito —dijo con esa voz ronca que arrastraba cada palabra—. Siempre tan caballeroso con las damas.
Elena no se inmutó. Ni siquiera lo miró. Mantuvo la vista fija en don Rodrigo como si Pedro fuera parte del mobiliario.
—Presidente Salinas —dijo con voz clara—. Entiendo que comprende la gravedad del incidente del sábado.
No fue una pregunta.
Don Rodrigo se acomodó nerviosamente en su silla, mirando de reojo a Pedro antes de responder.
—Así es, doña Elena. Todos queremos lo mejor para nuestros pueblos. La paz, la convivencia…
—La justicia —interrumpió Pedro. Aplastó su puro contra el borde del escritorio sin apartar los ojos de Juan—. También queremos justicia, ¿no es cierto, don Rodrigo?
El presidente tragó saliva.
Juan apretó ligeramente el respaldo de la silla de su madre, pero no dijo nada. Todavía no.
—Exacto, la justicia —respondió don Rodrigo, más por compromiso que por convicción. Se limpió el sudor del bigote—. Miren, es evidente que los roces entre estas dos familias importantes han ido escalando. Me enteré del altercado del sábado, de la golpiza a ese muchacho… Felipe, creo. Y del enfrentamiento que siguió.
Hizo una pausa, esperando que alguien objetara. Nadie lo hizo.
—La enemistad entre sus familias es más vieja que todos nosotros. No estoy aquí para remover el pasado. Las decisiones de mis predecesores son suyas; ni las comparto ni las juzgo.
Pedro soltó un gruñido de desaprobación. Juan notó que el presidente estaba evadiendo el tema del cambio de poder sobre San Guzmán que se llevó a cabo hace veinte años.
El viejo García desvió la mirada apenas un segundo.
—Lo que nos concierne ahora es el presente —continuó don Rodrigo con voz más aguda—. Evitar que esto escale a niveles incontrolables dentro del municipio de Santa Rita.
—Ve al grano, gordito —interrumpió el sicario junto a Pedro.
El presidente asintió con torpeza.
—Bien. Mi buen amigo don Andrés, residente de San Guzmán y cercano a la hacienda Moreno, me informó que la familia Moreno busca mi intervención para evitar una escalada de venganzas por este asunto.
Don Rodrigo Salinas tragó saliva antes de continuar.
—Propongo que escuchemos ambas versiones de lo ocurrido. Luego, en conjunto, decidiremos una solución justa para todos los involucrados.
Pedro encendió otro puro sin prisa. La llama del cerillo iluminó su rostro curtido, sus ojos grises. Dejó que el silencio se pudriera unos segundos.
—Primero las damas —dijo finalmente, señalando a Elena con el puro humeante.
Elena ajustó su rebozo negro con un movimiento preciso. Juan sintió cómo su madre respiraba hondo antes de hablar.
—El sábado por la noche —comenzó con voz clara—, cuatro hombres de los García pateaban a un muchacho en el suelo. Cuatro contra uno.
Pedro quitó la mirada de Juan y la clavó en Elena. Ella ni siquiera parpadeó. 
—Mis hijos intervinieron para detener una masacre. Actuaron de frente. Pero sus hombres, don Pedro, respondieron con la única tradición que parecen respetar: la cobardía. Sacaron las armas cuando se vieron superados por los puños. 
El silencio en la oficina se volvió sólido.
 —Si mi hijo Juan desenfundó, fue para evitar un asesinato a sangre fría.
Elena finalmente giró la cabeza hacia Pedro García. Sus ojos oscuros brillaron bajo la luz del quinqué.
—El señor aquí presente llegó después de eso. Amenazó a todo San Guzmán, señor presidente. Dijo que si alguien más tocaba lo que era de los García, mi hijo Juan tendría que tocar su guitarra en el funeral de esa persona.
Don Rodrigo tragó saliva audiblemente.
—Esa, señor presidente, es mi versión. Y puede verificarla con cualquiera de las treinta personas que estaban presentes esa noche.
El presidente miró a Pedro, en espera de su respuesta.
Pedro dejó que el silencio se extendiera unos segundos más. Encendió otro puro con calma, como si tuviera todo el tiempo del mundo.
—Hermosa historia, doña Elena —dijo finalmente, exhalando humo hacia el techo—. Casi tan hermosa como usted. Lástima que esté incompleta.
Don Rodrigo se tensó en su silla. Juan clavó los ojos en Pedro.
—Ese muchacho ofendió a mi sangre. —Pedro se inclinó hacia delante, sus ojos grises clavados en don Rodrigo—. Y la sangre se defiende, presidente. 
Hizo un gesto despectivo con la mano. 
—Luego llegó Luis Moreno haciendo teatro, buscando aplausos como siempre. Humilló a mi hijo frente al pueblo. Y cuando uno de los míos intentó recuperar algo de dignidad, se encontró con el cañón de Juan Moreno en la cara. 
Se recargó en la silla, desafiante. 
—Mis hijos cometieron el error de dejarse provocar. Pero los Moreno cometieron el error de creer que pueden humillar a un García sin pagar el precio.
Las palabras de Pedro estaban cargadas de una verdad a medias, pero cinceladas de mentiras y un victimismo barato. Juan sintió cómo la rabia subía por su garganta, pero la mano de su madre sobre la suya lo detuvo. 
—Y entonces llegué yo —dijo Pedro, recostándose en su silla con aire cansado—. Encontré a mis hijos sangrando, uno tirado en el suelo, otro con un arma temblando en la mano, y a los Moreno rodeados de medio pueblo armado. ¿Qué esperaban que hiciera? ¿Felicitarlos?
Exhaló otra bocanada de humo.
—Les dije que se fueran. A mis hijos, digo. Que volvieran al rancho caminando por hacerme quedar mal. Pero también le dije algo a la gente de San Guzmán, y lo repito aquí frente al presidente: si alguien vuelve a tocar lo que es mío, habrá consecuencias. Y no me disculpo por eso, porque un hombre que no defiende a su familia no es hombre.
Se puso de pie lentamente, apoyándose en el escritorio.
—Yo crié a catorce hijos, don Rodrigo. Catorce. Todos buenos para el trabajo y para defender nuestro nombre. Además, tengo a otras catorce familias que me siguen porque saben que no los abandono. Esas son veintiocho familias que dependen de mí, presidente. Y cuando los Moreno humillan a uno de los míos en público, me humillan a mí. Humillan a todos los que cargan mi apellido.
Caminó hacia la ventana, dándoles la espalda.
—¿Sabe qué pasó en San Miguel hace catorce años, don Rodrigo?
El presidente negó con la cabeza, nervioso.
—Dos familias importantes —continuó Pedro sin voltear—. Empezaron igual que nosotros. Un pleito por una muchacha, o por una cerca, ya ni se acuerda nadie. Tuvieron su reunión, como esta. Prometieron paz. Apretones de mano, palabras bonitas.
Giró lentamente, su silueta recortada contra la luz de la ventana.
—Pero alguien no aguantó las ganas. Alguien disparó primero. Y cuando eso pasa, don Rodrigo, ya no hay marcha atrás. Se mataron todos. Hombres, viejos, hasta los muchachos que apenas sabían montar. No quedó nadie de esas familias para enterrar a los muertos. Tuvieron que traer gente de otros pueblos.
El silencio en la oficina era absoluto.
—Yo no quiero que eso pase aquí —dijo Pedro, pero su voz no sonaba conciliadora. Sonaba como advertencia. Pero tampoco voy a dejar que los Moreno crean que pueden hacer lo que quieran sin consecuencias.
Volvió a su silla y se sentó con pesadez.
—Esa es mi versión, presidente. Y también puede verificarla. Con cualquiera de los míos que estaba ahí.
Don Rodrigo se limpió el sudor del bigote con un pañuelo arrugado. Sus manos temblaban ligeramente mientras lo doblaba y lo guardaba en el bolsillo de su chaleco.
—Bien, bien —dijo con voz demasiado aguda—. Creo que ambas versiones tienen… tienen sus puntos válidos. Lo importante aquí es encontrar un terreno común, ¿no es así? Una solución que beneficie a todos.
Miró a Elena, después a Pedro, esperando que alguien asintiera. Nadie lo hizo.
—Quizás podríamos establecer… no sé, una compensación. O tal vez un acuerdo escrito donde ambas familias se comprometan a mantener la distancia. Algo oficial, con sellos y firmas.
Pedro exhaló humo con lentitud, sus ojos grises fijos en el techo como si estuviera considerando la propuesta del presidente. Dejó que el silencio se extendiera hasta volverse incómodo.
—Don Rodrigo —dijo finalmente, con esa voz ronca que arrastraba cada palabra—. Usted y yo sabemos que los papeles no valen nada cuando hay sangre de por medio.
Se inclinó hacia delante, apoyando los codos sobre las rodillas.
—Yo no vine a buscar conflicto. Vine porque usted me lo pidió. Porque pensé que tal vez, solo tal vez, los Moreno entenderían que en este municipio no son los únicos que merecen respeto.
Don Rodrigo asintió rápidamente, como si eso fuera progreso.
—Exacto, exacto. El respeto mutuo es fundamental.
—Pero mire —continuó Pedro, señalando vagamente hacia la ventana—. Si realmente quisiéramos hablar de faltarle el respeto a alguien, empezaríamos por cómo los Moreno le faltan el respeto a la iglesia. El padre Matías me comentó hace poco que las donaciones de los Moreno han… ¿Cómo decirlo? Disminuido considerablemente.
Elena no se inmutó. Juan comprendió finalmente cuál era el plan de ataque de Pedro.
—Y no es solo el dinero —Pedro se recostó en su silla, disfrutando cada palabra—. Es que cada vez toman menos en cuenta al padre Matías para las decisiones del pueblo. Como si San Guzmán ya no fuera católico. Como si Dios se hubiera mudado cuando ustedes llegaron al poder.
El sicario junto a él soltó una risa breve. Don Rodrigo carraspeó incómodo.
—Bueno, yo no diría que…
—Y eso sí que es grave, don Rodrigo —interrumpió Pedro—. Porque un pueblo sin Dios es un pueblo sin orden. Y si los Moreno no respetan ni a la iglesia, ¿cómo van a respetar a…
Juan apretó el respaldo de la silla con más fuerza. Pedro estaba tejiendo una red, y si le dejaba terminar, don Rodrigo no tendría más remedio que ponerse de su lado. La religión era un arma poderosa en estas tierras, y el viejo lo sabía.
Era el momento.
—Ocho mil pesos.
La voz de Juan cortó el aire como un cuchillo.
Pedro se detuvo a media frase. Todos los ojos se volvieron hacia él.
Juan dio un paso adelante. Había permanecido en silencio durante toda la reunión, inmóvil como estatua detrás de su madre, pero ahora su presencia llenó el espacio. Puso dos libros de contabilidad sobre el escritorio con un golpe seco que hizo saltar a Don Rodrigo y tintinear el quinqué.
—Ocho mil pesos —repitió, abriendo el primer libro con movimientos precisos—. Eso es lo que su familia debe en impuestos atrasados, don Pedro. Tres años sin pagar.
Giró el libro para que don Rodrigo pudiera verlo. El presidente se inclinó hacia delante, entornando los ojos para leer los números bajo la luz temblorosa.
—Aquí están las fechas —continuó Juan, pasando las páginas con el dedo—. Aquí los montos. Aquí las notificaciones que se enviaron y que fueron ignoradas.
Pedro no se movió. No miró los libros. Solo observaba a Juan con esos ojos grises que no revelaban nada.
—¿Qué? ¿Cómo se nos pasó esto por alto? —preguntó el presidente con los ojos a punto de desbordarse.
Juan cerró el primer libro y abrió el segundo.
—Y si vamos a hablar de la iglesia, hablemos bien. Los García no han dado un solo peso al padre Matías en dos años. Ni para las fiestas patronales. Ni para reparaciones. Nada.
Dejó que las palabras cayeran como piedras.
—Así que antes de venir a hablar de respeto, don Pedro, tal vez debería preguntarse quién le falta el respeto a quién.
El silencio en la oficina era tan denso que se podía cortar. Don Rodrigo miraba los libros con la boca ligeramente abierta. El sicario, junto a Pedro, había dejado de sonreír.
Pedro García se puso de pie lentamente, con la pesadez de un hombre viejo que carga demasiados rencores. La silla rechinó contra el piso de baldosas. Sus ojos nunca abandonaron el rostro de Juan.
Don Rodrigo miraba los libros con la boca ligeramente abierta, pasando las páginas con dedos temblorosos.
—¿Cómo… cómo se nos pasó esto por alto? —murmuró, más para sí mismo que para los demás—. Tres años… ocho mil pesos…
—¿Vienes a amenazarme con papeles, muchacho?
La voz de Pedro cortó el aire como navaja. Peligrosamente baja. Peligrosamente calmada.
Juan dio dos pasos hacia delante. El espacio entre él y Pedro se redujo a menos de dos metros. A pesar de casi doblarle la edad, ambos hombres se sostenían con la misma rigidez, la misma quietud amenazante de quienes saben usar la violencia.
—No vine a amenazarte, don Pedro —respondió Juan sin levantar la voz—. Vine a recordarte que si tu plan era cuestionar el honor de mi familia, primero debiste asegurarte de que el tuyo estuviera limpio.
El sicario junto a Pedro se tensó en su silla. Elena permanecía inmóvil, observando a su hijo con esa serenidad que solo las madres que confían plenamente en sus hijos pueden tener.
Pedro exhaló despacio por la nariz, sus fosas nasales dilatándose. El puro en su mano temblaba ligeramente, no de miedo, sino de furia contenida.
—Crees que esos números significan algo, ¿verdad?
Dio un paso hacia Juan. Ahora estaban a un metro de distancia.
—El dinero se paga, muchacho. La sangre no.
Juan sostuvo la mirada de Pedro sin retroceder un centímetro. Los números habían funcionado —lo había visto en cómo Don Rodrigo miraba los libros con pánico—, pero Pedro seguía de pie, todavía peligroso.
Juan necesitaba que Pedro mostrara todas sus cartas ahora que estaba desprevenido, así que insistió.
Cuando habló, su voz era tan fría como el acero.
—Eso sí que suena a amenaza, Don Pedro.
Dio un paso más hacia delante, cerrando la distancia hasta quedar frente al viejo. A pesar de casi doblarle la edad, se miraban a los ojos como iguales.
—Y si vienes a mi pueblo, golpeas a mi gente, y encima amenazas con sangre… entonces ya no estamos hablando de respeto. Estamos hablando de guerra.
El sicario se puso de pie de golpe. Su silla cayó hacia atrás con un estruendo que hizo eco en la oficina estrecha. Su mano fue al cinturón, dedos envolviendo la empuñadura de su revólver.
Lo desenfundó.
No apuntó. Solo lo sacó, dejándolo caer junto a su pierna, el cañón apuntando al suelo. El metal brilló bajo la luz del quinqué. El mensaje era claro.
Juan no pensó. El metal brilló y él ya estaba encima. Un manotazo seco desvió el cañón hacia el techo; el segundo movimiento fue una garra directa a la garganta. El sicario ni siquiera gritó. Juan lo impactó contra la pared de adobe con un estruendo que hizo bailar el quinqué y llover polvo de las vigas. 
El revólver golpeó el suelo. 
Juan no aflojó. Lo mantuvo clavado contra el muro, asfixiándolo con el antebrazo, sus rostros a centímetros.
El tipo jadeaba, las manos arañando inútilmente el brazo de Juan. Sus ojos, normalmente fríos y amenazantes, ahora se abrían con sorpresa y falta de aire.
Juan inclinó su rostro a centímetros del sicario. Su voz salió baja, mortal, cargada de una furia contenida que había esperado toda la reunión para liberarse.
—Nadie. Escúchame bien, pendejo. Nadie desenfunda un arma en la misma habitación donde está mi madre.
El silencio en la oficina era absoluto. Solo se escuchaba el jadeo ahogado del sicario y el tintineo distante de las espuelas de alguien caminando afuera.
Pedro García no se había movido. Ni un paso. Ni un gesto. Se quedó exactamente donde estaba, de pie junto al escritorio, con el puro todavía humeando en su mano. Sus ojos grises no miraban a su hombre siendo estrangulado contra la pared.
Miraba a Elena.
Ella le devolvió la mirada con la misma serenidad con la que había entrado. No había parpadeo. No había sorpresa. Solo esa quietud implacable de quien sabía exactamente de lo que su hijo era capaz.
Don Rodrigo, en cambio, se había echado hacia atrás en su silla tan bruscamente que casi la volcaba. Su rostro había perdido todo el color. Las manos le temblaban sobre el escritorio, una de ellas todavía aferrada a los libros de contabilidad como si fueran su único salvavidas.
—Don Juan… por favor… —balbuceó con voz quebrada—. Esto… esto no es necesario…
Juan no respondió. No apartó los ojos del sicario. El hombre seguía arañando su brazo, con los pies raspando desesperadamente contra la pared en busca de apoyo que no existía. El sonido de las suelas contra el adobe era lo único que rompía el silencio.
Pedro exhaló una bocanada lenta de humo. Finalmente, habló.
—Suéltalo, muchacho.
No fue una súplica. Fue una orden tranquila, casi aburrida.
—Ya hiciste tu punto.
Juan no se movió. El sicario jadeaba con más dificultad ahora, sus manos perdiendo fuerza.
—Hijo.
La voz de Elena cortó el aire como una campana clara. Serena. Inapelable.
—Es suficiente.
Solo entonces Juan aflojó la presión. El sicario se desplomó contra la pared, resbalando hasta quedar de rodillas en el suelo, tosiendo y jadeando mientras se llevaba las manos al cuello. Juan retrocedió dos pasos, miró el revólver del suelo y lo pateó por debajo del escritorio de don Rodrigo. El arma giró sobre las baldosas hasta perderse en las sombras del rincón más alejado.
Se enderezó lentamente, ajustándose la chaqueta con las manos como si nada hubiera pasado. Su respiración era controlada, calmada. Como si estrangular a un hombre contra una pared fuera algo que hacía todos los días. Pero el gesto de acomodarse la ropa se alargó más de la cuenta. Sus dedos, al alisar la solapa, vibraban con un temblor fino, casi imperceptible. Era el precio a pagar. La reacción de su cuerpo al liberar la fuerza que mantenía encadenada. Con disimulo, apretó con fuerza la tela de la chaqueta entre los dedos, usando la presión para forzar a sus manos a la quietud antes de dejarlas caer a los costados.
Pedro observó todo con esos ojos grises que no revelaban nada. Dio una última calada a su puro antes de aplastarlo contra el borde del escritorio, esta vez con más fuerza de la necesaria. Las brasas se dispersaron sobre la madera oscura.
—Interesante —dijo finalmente, con una voz que intentaba sonar despreocupada, pero que arrastraba un filo cortante—. Parece que tu madre te ha enseñado bien, Juanito.
Caminó hacia su sicario, quien todavía respiraba con dificultad en el suelo. No le ofreció la mano. No lo ayudó a levantarse. Solo lo miró con algo que podría haber sido decepción o fastidio.
—Levántate —ordenó con sequedad—. Y recoge tu dignidad del suelo mientras lo haces.
El hombre obedeció con torpeza, apoyándose contra la pared para ponerse de pie. Su rostro había perdido toda la arrogancia anterior.
Pedro se giró hacia Don Rodrigo, ignorando completamente a Juan y Elena, como si ellos ya no merecieran ni su atención.
—Presidente Salinas —dijo con esa voz ronca que arrastraba cada palabra—. Creo que esta reunión ha llegado a su fin. Los papeles que trajo el muchacho… los revisaré con mi contador. Si hay deudas, se pagarán. Pero no porque los Moreno lo exijan, sino porque yo así lo decido.
Hizo una pausa, dejando que el silencio subrayara sus palabras.
—En cuanto al asunto del sábado… considero que ambas familias ya hemos demostrado nuestros puntos. Yo me aseguraré de que mis muchachos no vuelvan a San Guzmán sin mi permiso.
Finalmente, giró la cabeza hacia Juan. Sus ojos grises brillaron bajo la luz temblorosa del quinqué con algo peligroso, algo que no era miedo ni respeto, sino un reconocimiento frío de que había subestimado a su oponente.
—Pero que quede claro, Juan Moreno. Esto no se olvida.
No esperó respuesta. Se dirigió hacia la puerta con paso firme, su sicario arrastrándose detrás de él como sombra herida.
Antes de salir, Pedro se detuvo en el umbral sin voltear.
—San Miguel empezó así, don Rodrigo.
Y con eso, salió de la oficina. Sus pasos resonaron en el pasillo hasta desvanecerse en la distancia.
Don Rodrigo se quedó paralizado en su silla, mirando alternativamente los libros de contabilidad sobre su escritorio, el revólver en el rincón y la mancha de ceniza donde Pedro había aplastado su puro.
—Dios santo… —murmuró finalmente, limpiándose el sudor de la frente con manos temblorosas—. Dios santo, les prometo que no teníamos ni idea de que…
Elena sacudió su regazo, quitándose el polvo que cayó desde el techo. Se puso de pie con la misma serenidad con la que había permanecido sentada toda la reunión. Juan se acercó y le ofreció el brazo. Ella lo tomó con naturalidad.
—Presidente Salinas —dijo Elena con voz clara—. Espero que haya tomado nota de todo lo ocurrido aquí. Mi familia vino buscando justicia. Los García vinieron buscando intimidar.
Hizo una pausa, permitiendo que Don Rodrigo la mirara.
—Confío en que sabrá distinguir la diferencia.
No esperó respuesta. Salió de la oficina del brazo de su hijo, con la cabeza en alto y el rebozo negro ondeando suavemente detrás de ella.
Don Rodrigo se quedó solo en su oficina, rodeado de libros de contabilidad que lo acusaban, cenizas que lo advertían y un revólver olvidado en el rincón que le recordaba lo cerca que había estado todo de explotar.
Se sirvió un vaso de mezcal con manos temblorosas y se lo bebió de un trago.
Iba a ser un año muy largo.

Capítulo 4. El despacho.
Juan se permitió respirar con tranquilidad cuando finalmente entraron a las calles viejas y gastadas de San Guzmán. Cuando estaba fuera, aunque fuera por un par de horas, no podía evitar sentir una gran preocupación. Necesitaba saber cómo había ido el día en el campo, ver que los trabajadores habían regresado enteros, confirmar que ningún García había aprovechado su ausencia para causar problemas.
La camioneta avanzó despacio por el camino de tierra. El sol ya comenzaba su descenso detrás de las montañas, pintando el cielo de naranja y púrpura. Las sombras se alargaban sobre las casas de adobe, y el humo de las cocinas se elevaba perezoso hacia el atardecer.
Su madre no había dicho una palabra desde que salieron de Santa Rita. 
Mantenía la vista al frente, con las manos descansando sobre su regazo, el rebozo negro enmarcando su rostro como un retrato de serenidad. Pero Juan la conocía. Conocía esa quietud tensa, ese silencio que no era paz, sino procesamiento.
Él tampoco había hablado.
No sabía qué decirle. No sabía cómo explicar lo que había sentido cuando sus manos se cerraron alrededor del cuello de ese hombre. La facilidad con la que lo había levantado. La satisfacción oscura que le recorrió el pecho al ver el miedo en esos ojos que un segundo antes lo habían retado.
Su padre jamás habría hecho algo así.
Su padre habría encontrado otra forma. Siempre encontraba otra forma.
Juan apretó el volante con más fuerza de la necesaria. La camioneta dio un salto cuando pasó sobre un bache que podría haber esquivado fácilmente si hubiera estado prestando atención.
Pasaron frente a la cantina de José Luis. A través de las ventanas abiertas, Juan alcanzó a ver algunas figuras sentadas en las mesas. Escuchó risas apagadas, el tintineo de vasos, el rasgueo distante de una guitarra que no era la suya. La vida del pueblo seguía su curso, ajena a lo que había pasado en Santa Rita.
Giró hacia la calle principal que conducía a la hacienda. Los naranjos que flanqueaban el camino ya proyectaban sombras largas y negras sobre el empedrado. A lo lejos, divisó el portón de la hacienda Moreno, sus columnas de cantera alzándose contra el cielo como centinelas silenciosos.
Luis estaría esperándolos. Ángel también. Querrían saber todo. Querrían los detalles, las palabras exactas, las reacciones de Pedro García y de don Rodrigo.
La camioneta cruzó el portón principal. El patio central de la hacienda se extendía ante ellos, bañado en la luz dorada del atardecer. La fuente de cantera murmuraba su canción eterna. Las bugambilias de su madre se mecían suavemente con la brisa.
Y ahí, de pie junto a la fuente, estaban sus dos hermanos.
Luis se había quitado el sombrero y lo sostenía contra el pecho con ambas manos. Su postura era rígida, expectante. Ángel estaba a su lado, con los brazos cruzados, su rostro mostrando esa preocupación callada que lo caracterizaba.
Juan detuvo la camioneta frente a los escalones del portal. Apagó el motor. El silencio que siguió se sintió más pesado que todo el viaje de regreso.
Su madre puso una mano sobre su brazo antes de que él pudiera abrir la puerta.
—Hijo —dijo, mirándolo por primera vez desde que salieron de Santa Rita—. Lo que hiciste allá…
Juan esperó, sintiendo cómo su estómago se retorcía.
—Ese hombre quiso intimidarnos —continuó ella con voz pausada—. Solo quiero que sepas que ningún lazo, por más fuerte que sea, justifica actuar con rencor o coraje. Este pueblo no necesita otro líder fuerte físicamente; ya tiene a tu hermano. Trabaja con tu propia fuerza.
Las palabras cayeron sobre Juan como agua fría. No era reproche. Era peor que eso. Era recordatorio de quién debía ser y quién había sido en esa oficina.
—Madre, yo…
—Fin de la historia —repitió con firmeza—. No cargues con culpas que no te corresponden. Ya tienes suficiente peso sobre los hombros.
Bajó de la camioneta antes de que Juan pudiera responder. Luis se apresuró a ayudarla, ofreciéndole su brazo con una pequeña reverencia.
Juan se quedó sentado un momento más, con las manos todavía sobre el volante, mirando cómo sus hermanos rodeaban a su madre con preguntas que no alcanzaba a escuchar.
Respiró hondo una vez más.
Después bajó de la camioneta.

La familia Moreno entró al casón; ninguno hizo un comentario de más. Simplemente caminaron con tranquilidad hasta el que solía ser el despacho de don Francisco Moreno.
Cuando Juan abrió la puerta, el olor a madera de cedro y cuero viejo lo recibió como siempre. Era un aroma que no cambiaba, que se aferraba a las paredes como el último suspiro de su padre.
El despacho ocupaba la esquina suroeste del segundo piso, con dos ventanas amplias que daban al patio de los naranjos. La luz del atardecer entraba sesgada, proyectando rectángulos dorados sobre el piso de baldosas pulidas que su madre limpiaba religiosamente cada semana, aunque nadie usara la habitación.
El escritorio de nogal dominaba el centro: una pieza maciza con incrustaciones de latón en las esquinas y cajones que ya no rechinaban porque Elena los engrasaba con aceite de almendras cada mes. Sobre él descansaban exactamente las mismas cosas que su padre había dejado antes de morir: un tintero de cristal con la tinta seca y agrietada, una pluma fuente Parker que nunca nadie se atrevía a usar, un pisapapeles de cantera con el escudo de Jalisco tallado a mano, estado en el que había nacido.
Detrás del escritorio, la silla de respaldo alto esperaba vacía. Nadie se sentaba ahí. Ni siquiera Juan, que había heredado todo lo demás.
Las paredes estaban forradas de estantes de madera oscura, llenos de libros que su padre había coleccionado durante años: tratados de agricultura, códigos civiles de antes de la Revolución, una Biblia con páginas amarillentas y anotaciones en los márgenes con su letra apretada. En el estante superior, una hilera de botellas de cristal tallado contenía licores que nadie había probado: coñac francés, whisky escocés, mezcal de Oaxaca que su padre guardaba para ocasiones especiales que nunca llegaron.
En la pared norte, montado sobre dos ganchos de hierro forjado, descansaba el rifle de su padre. Un Winchester 1873 con la culata de nogal oscuro y el cañón pavonado en negro con incrustaciones doradas que formaban el nombre “Francisco” en letra cursiva cerca del guardamonte. Lo había usado durante la Revolución, cuando peleó junto a Villa en el norte. Después lo había colgado ahí, pulido, como recordatorio de lo que había sido y lo que había decidido dejar atrás.
Junto al rifle, enmarcadas en madera simple, colgaban tres fotografías descoloridas: su padre montado a caballo junto a otros revolucionarios, todos jóvenes y serios bajo sombreros anchos; su padre el día de su boda con Elena, ella con vestido blanco y él con traje de charro; y la última, tomada apenas dos años antes de su muerte, los cinco Moreno frente a la hacienda. Francisco con una mano sobre el hombro de Juan, Elena sosteniendo a Ángel de niño, Luis sonriendo con esa confianza que ya entonces lo caracterizaba y Carolina, de apenas veinte años, de pie junto a su padre con esa mirada seria que ya entonces prometía determinación.
Debajo de las fotografías, en un marco discreto de madera de nogal que hacía juego con el escritorio, colgaba un diploma:
“La Escuela de Enfermería del Hospital General de México otorga el título de Enfermera Titulada a
CAROLINA ELENA MORENO
México, Distrito Federal
15 de julio de 1935”

El sello oficial de la República brillaba opaco bajo la luz del atardecer. Las firmas eran ilegibles, salvo una al centro que rezaba “Hermanas de la Caridad de San Vicente de Paúl”.
Juan lo había visto mil veces. Seguía sin saber cuándo había aparecido exactamente en esa pared. Un día simplemente estaba ahí, colgado sin ceremonia ni explicación, como si siempre hubiera pertenecido al despacho de su padre a pesar de que su padre llevaba tres años muerto cuando Carolina se graduó.
Su madre lo había enmarcado. Su madre lo había colgado. Su madre nunca lo mencionó.
Y ninguno de los hermanos preguntó.
Porque preguntar significaría admitir la ausencia. Y admitir la ausencia significaría confrontar por qué ninguno le había pedido que volviera. Por qué ninguno fue a su graduación. Por qué la familia se fracturó sin una pelea, sin gritos.
Juan apartó la mirada del diploma y la dirigió hacia la vitrina.
En la esquina opuesta, una vitrina de cristal guardaba los recuerdos más preciados de su padre: cartuchos sin usar de la Revolución, una medalla que Villa le había dado personalmente, el machete con el que había cortado caña en sus primeros años como trabajador antes de heredar las tierras, un rosario de madera que había pertenecido a su madre.
Todo estaba exactamente donde su padre lo había dejado.
Todo excepto el hombre que le daba sentido a esa habitación.
El vacío que había dejado su presencia era palpable en el aire. Se sentía en el pueblo entero, pero ahí, en esa oficina… era asfixiante.
Juan entró primero, seguido por su madre y sus hermanos. Luis cerró la puerta despacio, y el clic del pestillo resonó en el silencio como un disparo lejano.
Elena caminó hasta la ventana y se quedó ahí, de espaldas a todos, mirando hacia los naranjos donde las sombras ya comenzaban a tragarse la luz.
Luis y Ángel se recargaron contra los estantes, esperando. Ninguno se sentó. En esta habitación, nadie se sentaba nunca.
Juan permaneció de pie frente al escritorio de su padre, con las manos apoyadas sobre la superficie pulida, sintiendo el peso de tres pares de ojos sobre él.
Luis, como siempre, rompió el silencio de la habitación:
—Entonces, ¿le diste en su madre a ese Pedro?
Juan soltó una risa breve.
—No del todo.
—No seas humilde, Juan —interrumpió su madre sin voltear, todavía mirando por la ventana—. Lo que hiciste fue una muestra de inteligencia.
Las palabras de su madre aliviaron el peso en sus hombros. Finalmente, sonrió.
—Pues, sí. Pero debo admitir que lo que logré fue gracias a la información de Ángel.
Ángel dejó escapar una sonrisa tímida, casi sorprendido del reconocimiento.
—¿Dónde conseguiste esos libros, hermano? Ni el propio presidente estaba al tanto de esa deuda.
—El domingo le pedí a don Aurelio que me acompañara a Santa Rita. Usé el antiguo gafete de papá para meterme al archivo de la oficina de gobierno.
Luis se enderezó, apartándose del estante con genuina sorpresa.
—¿Fuiste tú solo? ¿Tú?
—No, no solo. Con don Aurelio —respondió Ángel, encogiéndose de hombros como si no fuera gran cosa.
—Ángel —dijo Luis, sacudiendo la cabeza con una mezcla de admiración y burla—. Tú, que no sales ni para ir a misa, ¿te metiste a husmear en archivos del gobierno?
—Alguien tenía que hacerlo —respondió Ángel con simpleza—. Juan necesitaba algo más que palabras bonitas para enfrentar a Pedro. Y los números no mienten.
—Está bien, pero cuéntanos. —Luis se inclinó hacia delante con curiosidad—. ¿Cómo reaccionó el viejo cuando le pusiste los libros enfrente?
—Se quedó callado —respondió Juan—. Mirándome con esos ojos grises que tiene, como si quisiera matarme ahí mismo. Don Rodrigo casi se cae de la silla. Pedro dijo que revisaría los números con su contador, que pagaría si había deuda… pero no porque nosotros lo exigiéramos.
—Orgulloso hasta el final —murmuró Ángel.
—Sí —dijo Juan—. Y al salir, mencionó San Miguel.
El silencio que siguió fue pesado. Todos conocían la historia de San Miguel. Dos familias poderosas que se mataron entre sí hasta no dejar a nadie con vida.
—Eso no va a pasar aquí —cortó Luis.
—No —confirmó Juan con firmeza—. No voy a permitirlo.
—No vamos a permitirlo, querrás decir —corrigió Luis.
Elena finalmente se giró desde la ventana, apoyándose contra el marco. Una sonrisa pequeña pero genuina se dibujaba en su rostro, aunque sus ojos miraban más allá de sus hijos, hacia algún punto invisible.
—Tu padre estaría orgulloso —dijo con voz suave—. De los cuatro.
El silencio que siguió fue diferente al anterior. Más pesado. Luis dejó de recargarse contra el estante. Ángel bajó la mirada. Juan mantuvo los ojos fijos en su madre, esperando.
Siempre eran tres. Desde hacía once años, siempre eran tres.
—Recibí carta de Carolina esta semana —continuó Elena, como si no hubiera notado la tensión—. Pregunta cómo están. Me cuenta del hospital, de los pacientes que salvó, de las técnicas nuevas que está aprendiendo. Escribe con tanta pasión sobre su trabajo…
Luis se cruzó de brazos, su semblante cambiando a algo más nostálgico, más incómodo. Juan notó cómo evitaba mirar el diploma en la pared.
—¿Y qué le respondiste? —preguntó Juan, su voz más neutral que curiosa.
—La verdad. Que están bien. Que están cumpliendo con su deber, como ella con el suyo —Elena hizo una pausa—. También le conté del pleito con los García. Pensé que tenía derecho a saber.
—¿Para qué? —La voz de Luis sonó más cortante de lo que pretendía—. No es como si pudiera hacer algo desde allá.
Elena lo miró con esa expresión que solo las madres tienen: mezcla de reproche y comprensión infinita.
—Porque es su familia, Luis. Porque aunque esté a cientos de kilómetros, sigue siendo tu hermana. Y porque ella pregunta por ustedes en cada carta, aunque ustedes no pregunten por ella.
Luis bajó la mirada. Ángel se movió incómodo en su lugar. Juan permaneció inmóvil, procesando.
—No es que no preguntemos, madre —dijo Ángel con voz pequeña—. Es que… ya no sé qué preguntar. Tenía siete años cuando se fue. Apenas la recuerdo.
—Yo sí la recuerdo —murmuró Luis—. Recuerdo que se fue.
La frase cayó como piedra en agua quieta. Elena cerró los ojos un momento, dolida.
—Se fue porque su padre se lo pidió —dijo con firmeza, mirando directamente a Juan—. Juan lo sabe mejor que nadie.
Juan sostuvo la mirada de su madre. Sí, lo sabía. Había estado ahí, en esa habitación que olía a muerte y medicina. Había escuchado a su padre explicar por qué Carolina debía irse, por qué era necesario. Lo sabía. Y eso no hacía que doliera menos.
—Alguien tenía que aprender a salvar vidas mientras ustedes aprendían a protegerlas —continuó Elena—. No nos abandonó. Se sacrifica día con día.
—Lo sabemos, madre —dijo Juan con voz controlada, pero había un filo.
Hizo una pausa, sintiendo cómo Luis y Ángel lo miraban.
—Pero once años, madre. Once años cuidando extraños. Padre le pidió que se fuera para estudiar, no que nunca volviera. ¿Dónde estaba cuando Luis se rompió el brazo? ¿Cuándo Ángel tuvo fiebre que casi lo mata? ¿Cuándo tú...?
Se detuvo.
Elena caminó hasta Juan y puso una mano en su mejilla con ternura.
—¿Y tú dónde estabas, hijo? En los campos. ¿Luis? Junto a ti, complementando tu liderazgo. ¿Ángel? En la iglesia, con sus libros. Todos cumpliendo sus deberes. Ella cumple el suyo en otro lugar. Eso no la hace menos Moreno.
—Pero nos hace estar divididos —cortó Luis, su voz cargada de algo que sonaba peligrosamente cercano a resentimiento—. Pedro García tiene razón en eso. Estamos divididos, madre.
Elena se tomó su tiempo para responder. Caminó de regreso a la ventana, mirando hacia el horizonte, hacia donde sabía que su hija velaba por vidas que no conocía mientras su familia peleaba batallas sin ella.
—Divididos... —repitió como probando la palabra—. ¿Eso creen? ¿Que porque Carolina eligió un deber diferente están divididos?
Se giró, y ahora sus ojos brillaban con algo más que nostalgia. Había determinación ahí.
—Su hermana escribe constantemente. Cada mes sin falta. Me cuenta de su trabajo, me pregunta por ustedes, me manda dinero cuando puede. ¿Y saben qué encuentro cuando le llevo sus cartas?
Miró a cada uno directamente.
—Sobres sin abrir. Porque ninguno de ustedes se molesta en leerlas.
Luis se tensó. Ángel se sonrojó de vergüenza. Juan sostuvo la mirada de su madre, pero no dijo nada.
—Yo leo cada palabra que escribe —continuó Elena, su voz quebrándose ligeramente—. Leo cómo extraña las bugambilias del patio. Cómo pregunta si Luis sigue siendo el más elegante del pueblo. Cómo quiere saber qué libros lee Ángel ahora. Cómo me pide que le diga a Juan que está orgullosa de él, de cómo mantiene unida a la familia.
Hizo una pausa dolorosa.
—Y yo le respondo que están bien. Que están juntos. Que la extrañan. Porque no puedo decirle la verdad: que sus hermanos la borraron como si nunca hubiera existido.
El silencio era asfixiante.
—Madre, no es así... —comenzó Ángel.
—¿No? —Elena lo interrumpió con suavidad—. ¿Cuándo fue la última vez que alguno de ustedes mencionó su nombre sin que yo lo hiciera primero?
Nadie respondió.
—Carolina salvó diecisiete vidas el mes pasado. Diecisiete personas que volvieron con sus familias porque ella supo qué hacer. ¿Y saben qué me escribió después de contarme eso? Me preguntó si eso era suficiente. Si salvar diecisiete extraños compensaba no haber estado aquí para cuidar de ustedes.
Elena se limpió una lágrima que no quería derramar.
—Así que no me vengan a decir que están divididos. Ustedes eligieron la división. Carolina eligió su deber. Hay una diferencia.
Juan intercambió miradas con sus hermanos. Luis asintió primero, casi por obligación, pero había culpa en sus ojos. Después, Ángel, quien no podía sostener la mirada de su madre.
—Juntos —dijo Juan finalmente, con voz firme pero no convencida—. Vamos a mantenernos juntos.
Elena los miró a los tres, y aunque sonrió, era una sonrisa triste.
—Entonces lean sus cartas. Respóndanle. Porque el día que la necesiten de verdad, hijos, y ella no esté... va a ser porque ustedes la empujaron tan lejos que no encontró el camino de regreso.
Se apartó de la ventana, su postura recuperando esa firmeza que la caracterizaba.
—Claro que no vamos a permitir lo de San Miguel. Su padre nos heredó una enorme responsabilidad hacia esta gente y nuestro trabajo como guardianes es mantenernos unidos. Hombro con hombro.
Elena clavó la mirada en Luis hasta que este asintió en aprobación.
—Mientras no dejen que el orgullo o la desconfianza los separe, los García no tienen ninguna oportunidad contra ustedes. Pero si se dividen, Pedro habrá ganado sin disparar un solo tiro.
Se mantuvo firme, como dejando que sus palabras calaran profundo en sus hijos.
—Voy a organizar un baile el próximo sábado. Quiero que el pueblo vea que los Moreno siguen siendo una familia. Aunque estemos incompletos.
Los tres hermanos se quedaron en silencio. La palabra “incompletos” resonó en el despacho como campana.
Luis fue el primero en hablar, su voz apenas un murmullo.
—Mañana leo su carta.
Ángel asintió.
—Yo también.
Juan miró el diploma en la pared. Carolina Elena Moreno. 15 de julio de 1935.
Once años de cartas no leídas. Once años de una hermana que existía solo en palabras que nadie abría.
—Deberíamos haberla celebrado por su graduación —dijo Juan, más para sí mismo.
Nadie respondió. Elena se mantuvo junto a la ventana, disimulando una sonrisa al notar el cambio en los hermanos.
Se quedaron un momento pensando, cada uno interiorizando sus pensamientos. Finalmente, Juan rompió la tensión, desviando la conversación hacia territorio más seguro:
—Le pediré a Lupita que te ayude a organizar el baile, Madre.
—¡No! —interrumpió Luis demasiado rápido—. Yo se lo pido, yo les ayudo.
Todos lo miraron extrañados por su repentina intervención.
—Quiero decir... yo puedo pedírselo... si quieren.
Un silencio incómodo llenó el despacho. Elena arqueó una ceja. Juan intercambió una mirada con Ángel.
—¿Desde cuándo te ofreces voluntario para organizar fiestas? —preguntó Juan con cautela.
—Desde... desde ahora —respondió Luis, ajustándose el sombrero con nerviosismo—. Es que... Lupita y yo... bueno, ella es muy eficiente y yo sé exactamente lo que necesita el pueblo para distraerse después de todo esto.
—Ajá —dijo Ángel, sin poder ocultar una sonrisa—. Muy conveniente, hermano.
Luis le lanzó una mirada de advertencia.
—No empieces, Ángel.
—No empiezo nada —respondió Ángel con inocencia fingida—. Solo digo que tal vez deberías dejar de ser tan... Don Juan. Ya tenemos uno, literalmente.
Juan soltó una carcajada que resonó en el despacho. Elena se llevó una mano a la boca para ocultar su sonrisa. La tensión de momentos antes se disolvía con el alivio de la risa compartida.
Luis señaló a Ángel con el dedo.
—Tú cállate. ¿Qué me vas a venir a decir a mí si tú nunca has amado? Yo no tengo la culpa de ser... un hombre de sangre caliente. Un amante nato.
—Pero eso no quita que ahora estés rojo como tomate.
—No estoy rojo.
—Estás del color del mole de madre.
Juan tuvo que apoyarse en el escritorio de tanto reír. Elena sacudió la cabeza, pero sus ojos brillaban con diversión. Era exactamente esto lo que necesitaban después de la pesadez de la conversación sobre Carolina.
—Está bien, Luis —dijo finalmente—. Tú habla con Lupita. Pero que sea para el baile, no para otras cosas. Ya me cansé de pedir disculpas a las familias por tus cortejos fugaces.
—Sí, madre —respondió Luis, recuperando algo de su compostura—. Solo para el baile.
Elena los miró a los tres una última vez antes de salir del despacho. Sus hijos. Incompletos sin su hermana, pero juntos al fin y al cabo.
Tal vez mañana leerían las cartas de Carolina.
Tal vez era un comienzo.

Al salir la familia y llegar a la sala principal del casón, el padre Matías esperaba de pie junto a uno de los arcos, observando con aparente fascinación un retrato al óleo de don Francisco Moreno que colgaba en la pared.
—Padre Matías —saludó Elena con sorpresa—. No sabíamos que había llegado.
El padre se giró, dejando ver su rostro curtido por los años y esa sonrisa cálida que siempre lo caracterizaba.
—Doña Elena, hijos —dijo mientras hacía una leve reverencia—. Discúlpenme por presentarme sin avisar. Rosa me dejó pasar cuando llegué. Me dijo que estaban en el despacho y preferí esperarlos aquí.
Elena caminó hasta él y lo tomó por el brazo con afecto genuino.
—Usted sabe que su presencia siempre es bienvenida en esta casa, padre. No necesita disculparse.
—Es usted muy amable —respondió el padre, dándole unas palmaditas en la mano—. Me enteré por algunos feligreses de que hubo... cierta tensión con los García hace unos días. Solo quería asegurarme de que todos estuvieran bien.
—Tuvimos un desacuerdo, padre —dijo Juan, acercándose—. Nada que no se pueda manejar.
—Ah, los García —suspiró el padre, negando con la cabeza—. Esa familia y la suya llevan décadas bailando el mismo baile. Siempre espero que algún día encuentren la forma de... bueno, de dejar de bailar.
Luis soltó una risa breve.
—Con todo respeto, padre, pero creo que ese baile solo termina cuando uno de los dos deja de existir.
—Que Dios no lo permita —respondió el padre Matías, persignándose—. Aunque debo admitir que don Pedro no ha pisado mi iglesia en meses. Es difícil interceder por la paz cuando una de las partes se aleja de Dios.
Elena suspiró.
—Hoy fuimos a Santa Rita, padre. El presidente Salinas prometió mediar en esto.
—¿El presidente Salinas? —el padre arqueó las cejas con genuina sorpresa—. No esperaba que don Rodrigo se involucrara en asuntos familiares. Ese hombre prefiere mantenerse... neutral, diría yo.
—Digamos que la situación lo obligó —respondió Juan sin dar más detalles.
El padre Matías asintió lentamente, como procesando la información.
—Entiendo. Bueno, espero que su intervención ayude a calmar las aguas. ¿Y ustedes? ¿Planean tomar alguna medida adicional? No sé, quizás vigilar más el pueblo, establecer turnos...
Juan intercambió una mirada rápida con Luis antes de responder.
—Por ahora creemos que lo mejor es mantener la rutina, padre. No queremos que la gente sienta que hay más tensión de la que realmente existe.
—Además —añadió Ángel—, la falta de lluvias ya tiene al pueblo bastante preocupado. No queremos añadir más inquietud.
—Claro, claro —dijo el padre, asintiendo con comprensión—. Ustedes siempre pensando en el bienestar del pueblo. Es admirable.
Hubo una pausa breve. El padre Matías miró hacia la puerta, como si estuviera a punto de despedirse, pero entonces se detuvo.
—Aunque, si me permiten la observación... a veces la rutina puede volverse peligrosa cuando hay amenazas reales. Don Pedro no es conocido por su paciencia.
—Lo tenemos en cuenta, padre —respondió Juan con firmeza—. Pero también sabemos que los García no son tontos. Una cosa es provocar, otra muy distinta es atacar.
—Tienen razón, tienen razón —el padre levantó las manos en señal de paz—. Perdonen a este viejo por entrometerse en asuntos que no le corresponden. Solo me preocupo por todos ustedes.
Elena le apretó el brazo con cariño.
—Y se lo agradecemos, padre. Su preocupación es una bendición para esta familia.
El padre Matías sonrió y finalmente se dirigió hacia la puerta. Juan lo acompañó, abriéndole el portón principal. La luz del atardecer entraba sesgada, proyectando la sombra alargada del sacerdote sobre las baldosas.
—Recen por la paz, hijos —dijo el padre desde el umbral—. Y si necesitan hablar, mi confesionario siempre está abierto. A veces compartir nuestras cargas con Dios alivia el peso.
—Gracias, padre —respondieron los tres hermanos casi al unísono.
El padre Matías se alejó por el camino de tierra con su paso lento pero seguro, su sotana negra ondeando ligeramente con la brisa.
Juan cerró la puerta y se giró hacia sus hermanos. Luis y Ángel lo miraban con expresiones idénticas de desconcierto.
—¿No les pareció raro? —preguntó Luis en voz baja.
—¿Qué cosa? —respondió Elena, ya caminando hacia la cocina.
—Las preguntas del padre. Sobre nuestros planes, sobre los patrullajes…
Elena se detuvo y se giró con una expresión entre divertida y reprobatoria.
—Luis, el padre Matías ha cuidado de este pueblo por veinte años. Es su trabajo saber qué pasa, preocuparse por todos. Si no preguntara, entonces sí me preocuparía.
—El padre siempre ha sido preguntón —dijo Juan, queriendo cerrar el tema. Elena los empujó suavemente hacia la cocina. —Anden, el mole se enfría. Luis y Juan obedecieron, pero Ángel se quedó un segundo más mirando la madera cerrada del portón. El padre Matías nunca preguntaba por patrullas. Nunca. Ángel sintió un frío que no tenía nada que ver con el atardecer, se persignó rápido y corrió para alcanzar a sus hermanos.
        """
        # ============================================
        # CAMBIO 2: Regex más robusto y compatible con librería 'regex'
        # ============================================
        # Detectamos Prólogo, Capítulo X y también Acto X (visto en tu texto)
        chapter_pattern = r'(Prólogo|Capítulo \d+[^\n]*|Acto \d+[^\n]*)'
        
        # La librería 'regex' maneja el split con lookahead igual, pero es más segura
        original_chapters = re.split(f'(?={chapter_pattern})', sample_text)
        
        final_list = []
        global_id = 1 

        for raw_chapter in original_chapters:
            if not raw_chapter.strip():
                continue

            lines = raw_chapter.strip().split('\n')
            title = lines[0].strip()
            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            if len(content.split()) < 50:
                continue

            if len(content) > MAX_CHARS_PER_CHUNK:
                logging.warning(f"⚠️ Fragmentando '{title}'...")
                sub_chunks = smart_split(content, MAX_CHARS_PER_CHUNK)
                
                for idx, chunk in enumerate(sub_chunks):
                    final_list.append({
                        'id': global_id,
                        'title': f"{title} (Parte {idx + 1}/{len(sub_chunks)})",
                        'content': chunk,
                        'word_count': len(chunk.split()),
                        'is_fragment': True,
                        'parent_chapter': title # <--- Requisito cumplido
                    })
                    global_id += 1
            else:
                # CAMBIO 3: Consistencia en metadatos
                final_list.append({
                    'id': global_id,
                    'title': title,
                    'content': content,
                    'word_count': len(content.split()),
                    'is_fragment': False,
                    'parent_chapter': title # <--- AÑADIDO: Vital para que no falle la agrupación
                })
                global_id += 1

        logging.info(f"📚 Libro segmentado en {len(final_list)} unidades.")
        return final_list
        
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        raise