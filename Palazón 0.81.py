import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.animation import Animation
import threading
from typing import Dict, Tuple, Optional
from bisect import bisect_right

# Configuración de ventana para Android
Window.softinput_mode = 'below_target'

# --- CONSTANTES Y CONFIGURACIÓN ---
class UIConstants:
    """Constantes de estilo y colores"""
    COLOR_HEADER = '#0F766E'
    COLOR_SUCCESS = '#10B981'
    COLOR_RESET = '#6B7280'
    COLOR_SECONDARY = '#3B82F6'
    COLOR_DANGER = '#DC2626'
    COLOR_WARNING = '#F59E0B'
    COLOR_BG_LIGHT = '#F8F9FA'
    COLOR_TEXT_DARK = '#1F2937'
    COLOR_CARD_BG = '#EFF6FF'
    
    # Clasificaciones con colores
    CLASIFICACION_COLORES = {
        'Bajo': '#059669',    # Verde
        'Medio': '#F59E0B',   # Amarillo
        'Alto': '#DC2626'     # Rojo
    }

class Config:
    """Configuración de negocio"""
    VALOR_TOTAL = 58362
    ANCHURA_SURCO = 1.65
    M2_POR_HECTAREA = 10000
    NIVELES_COMPLEJIDAD = {
        2: 58362, 3: 64847, 4: 72952, 5: 83374, 6: 97270,
        7: 116724, 10: 145905, 12: 166749, 14: 194541, 
        15: 216156, 16: 233449, 17: 265283, 28: 291811, 
        39: 343308, 55: 389082, 65: 486353, 75: 583623,
        85: 833748, 100: 1167247
    }
    
    # Cache de niveles ordenados para búsqueda binaria
    NIVELES_KEYS = sorted(NIVELES_COMPLEJIDAD.keys())
    
    DEBOUNCE_DELAY = 0.3  # segundos

# --- MOTOR DE CÁLCULO OPTIMIZADO ---
class CalculoEngine:
    """Motor de cálculos optimizado con caché"""
    
    def __init__(self):
        self.niveles_cache = self._construir_cache()
    
    def _construir_cache(self) -> list:
        """Pre-construye lista de niveles para búsqueda rápida"""
        return sorted(Config.NIVELES_COMPLEJIDAD.items())
    
    @staticmethod
    def validar_entrada(valor_str: str, max_val: float = float('inf')) -> float:
        """Valida y convierte entrada del usuario"""
        try:
            if not valor_str:
                return 0.0
            val = float(valor_str)
            return max(0.0, min(val, max_val))
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calcular_valor_modificado(guinea: float, caminadora: float) -> Tuple[float, float]:
        """Calcula valores modificados"""
        if guinea > 0:
            guinea *= 2
        caminadora *= 0.82
        return guinea, caminadora
    
    def obtener_nivel_y_valor(self, porcentaje: float) -> Tuple[Optional[int], Optional[float]]:
        """Obtiene nivel y valor usando búsqueda binaria (O(log n))"""
        idx = bisect_right(Config.NIVELES_KEYS, porcentaje)
        if idx < len(Config.NIVELES_KEYS):
            nivel = Config.NIVELES_KEYS[idx]
            return nivel, Config.NIVELES_COMPLEJIDAD[nivel]
        return None, None
    
    @staticmethod
    def calcular_surcos(valor_ha: float, largo_surco: float) -> float:
        """Calcula número de surcos necesarios"""
        if valor_ha <= 0 or largo_surco <= 0:
            return 0
        valor_m2 = valor_ha / Config.M2_POR_HECTAREA
        if valor_m2 == 0:
            return 0
        m2_a_pagar = Config.VALOR_TOTAL / valor_m2
        return m2_a_pagar / (Config.ANCHURA_SURCO * largo_surco)
    
    @staticmethod
    def obtener_clasificacion(porcentaje: float) -> str:
        """Obtiene clasificación según porcentaje"""
        if porcentaje <= 14:
            return "Bajo"
        elif porcentaje <= 25:
            return "Medio"
        return "Alto"
    
    @staticmethod
    def obtener_color_clasificacion(clasificacion: str) -> str:
        """Retorna color para clasificación"""
        return UIConstants.CLASIFICACION_COLORES.get(clasificacion, UIConstants.COLOR_TEXT_DARK)
    
    def procesar_calculo(self, guinea: float, caminadora: float, bledo: float, 
                        enredadera: float, marihuano: float, largo_surco: float) -> Tuple[Optional[Dict], Optional[str]]:
        """Procesa cálculo completo"""
        guinea_mod, caminadora_mod = self.calcular_valor_modificado(guinea, caminadora)
        porcentaje = sum([guinea_mod, caminadora_mod, bledo, enredadera, marihuano])
        
        if porcentaje > 100.01:
            return None, "⚠️ El porcentaje supera el 100%"
        
        nivel, valor_ha = self.obtener_nivel_y_valor(porcentaje)
        if nivel is None:
            return None, "❌ Porcentaje fuera de rango"
        
        surcos = self.calcular_surcos(valor_ha, largo_surco)
        clasificacion = self.obtener_clasificacion(porcentaje)
        color = self.obtener_color_clasificacion(clasificacion)
        
        return {
            'porcentaje': porcentaje,
            'nivel': nivel,
            'valor_ha': valor_ha,
            'surcos': surcos,
            'clasificacion': clasificacion,
            'color_clasificacion': color
        }, None

# --- INTERFAZ KV MEJORADA ---
KV_STRING = '''
#:import hex kivy.utils.get_color_from_hex
#:import Animation kivy.animation.Animation

<ModernInput@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: "75dp"
    text_label: ""
    input_id: ""
    default_text: ""
    spacing: "8dp"
    padding: "10dp"
    
    canvas.before:
        Color:
            rgba: hex('#F8F9FA')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8,]

    Label:
        text: root.text_label
        size_hint_y: None
        height: "25dp"
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        color: hex('#1F2937')
        font_size: '14sp'
        bold: True

    TextInput:
        id: ti
        text: root.default_text
        multiline: False
        input_filter: 'float'
        write_tab: False
        background_normal: ''
        background_color: 1, 1, 1, 1
        foreground_color: hex('#111827')
        padding: [15, 12]
        size_hint_y: None
        height: "42dp"
        font_size: '16sp'
        hint_text_color_focus: hex('#A0AEC0')

<CalculadoraRoot>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: hex('#FFFFFF')
        Rectangle:
            pos: self.pos
            size: self.size

    # --- Header ---
    BoxLayout:
        size_hint_y: None
        height: "85dp"
        orientation: 'vertical'
        padding: "15dp"
        spacing: "5dp"
        canvas.before:
            Color:
                rgba: hex('#0F766E')
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: "Calculadora Palazón"
            font_size: '26sp'
            bold: True
            color: 1, 1, 1, 1
            size_hint_y: None
            height: "35dp"
        
        Label:
            text: "Análisis de Complejidad Agrícola"
            font_size: '12sp'
            color: hex('#D1FAE5')
            size_hint_y: None
            height: "25dp"

    # --- ScrollView con contenido ---
    ScrollView:
        bar_width: "6dp"
        bar_color: hex('#3B82F6')
        
        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            padding: "12dp"
            spacing: "10dp"

            # --- Sección: Inputs de Malezas ---
            Label:
                text: "📊 Composición de Malezas (%)"
                size_hint_y: None
                height: "30dp"
                font_size: '14sp'
                bold: True
                color: hex('#0F766E')

            ModernInput:
                id: inp_guinea
                text_label: "Guinea"
            
            ModernInput:
                id: inp_caminadora
                text_label: "Caminadora"
            
            ModernInput:
                id: inp_bledo
                text_label: "Bledo"
            
            ModernInput:
                id: inp_enredadera
                text_label: "Enredadera"
            
            ModernInput:
                id: inp_marihuano
                text_label: "Marihuano"

            # --- Indicador de Progreso ---
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "50dp"
                spacing: "5dp"

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: "20dp"
                    spacing: "5dp"

                    Label:
                        text: "Progreso:"
                        size_hint_x: 0.3
                        font_size: '12sp'
                        color: hex('#0369A1')

                    Label:
                        id: label_porcentaje_progreso
                        text: "0.0%"
                        size_hint_x: 0.7
                        font_size: '12sp'
                        color: hex('#0369A1')

                ProgressBar:
                    id: progress_bar
                    max: 100
                    value: 0
                    size_hint_y: None
                    height: "8dp"
                    canvas.before:
                        Color:
                            rgba: (1, 0, 0, 1) if self.value > 100 else (0.06, 0.6, 0.4, 1)

            # --- Sección: Configuración ---
            Label:
                text: "⚙️ Configuración"
                size_hint_y: None
                height: "30dp"
                font_size: '14sp'
                bold: True
                color: hex('#0F766E')

            ModernInput:
                id: inp_largo
                text_label: "Longitud Surco (metros)"
                default_text: "100"

            # --- Botones ---
            GridLayout:
                cols: 2
                size_hint_y: None
                height: "55dp"
                spacing: "10dp"
                padding: [0, 10, 0, 0]

                Button:
                    text: "✓ CALCULAR"
                    background_normal: ''
                    background_color: hex('#10B981')
                    font_size: '15sp'
                    bold: True
                    canvas.before:
                        Color:
                            rgba: self.background_color
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [8,]
                    on_release: root.calcular()

                Button:
                    text: "↻ REINICIAR"
                    background_normal: ''
                    background_color: hex('#6B7280')
                    font_size: '15sp'
                    bold: True
                    canvas.before:
                        Color:
                            rgba: self.background_color
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [8,]
                    on_release: root.reiniciar()

            # --- Resultados ---
            Label:
                text: "📈 Resultados"
                size_hint_y: None
                height: "30dp"
                font_size: '14sp'
                bold: True
                color: hex('#0F766E')

            # Card Porcentaje
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "65dp"
                padding: [12, 10]
                spacing: "3dp"
                canvas.before:
                    Color:
                        rgba: hex('#EFF6FF')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Label:
                    text: "Porcentaje Total"
                    size_hint_y: None
                    height: "18dp"
                    color: hex('#0369A1')
                    font_size: '11sp'
                    bold: True
                Label:
                    id: value_porcentaje
                    text: "0.00%"
                    size_hint_y: None
                    height: "30dp"
                    color: hex('#1F2937')
                    font_size: '18sp'
                    bold: True
                    text_size: self.size
                    halign: 'left'

            # Card Nivel
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "65dp"
                padding: [12, 10]
                spacing: "3dp"
                canvas.before:
                    Color:
                        rgba: hex('#EFF6FF')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Label:
                    text: "Nivel de Complejidad"
                    size_hint_y: None
                    height: "18dp"
                    color: hex('#0369A1')
                    font_size: '11sp'
                    bold: True
                Label:
                    id: value_nivel
                    text: "-"
                    size_hint_y: None
                    height: "30dp"
                    color: hex('#1F2937')
                    font_size: '18sp'
                    bold: True

            # Card Valor
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "65dp"
                padding: [12, 10]
                spacing: "3dp"
                canvas.before:
                    Color:
                        rgba: hex('#EFF6FF')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Label:
                    text: "Valor por Hectárea"
                    size_hint_y: None
                    height: "18dp"
                    color: hex('#0369A1')
                    font_size: '11sp'
                    bold: True
                Label:
                    id: value_valor
                    text: "-"
                    size_hint_y: None
                    height: "30dp"
                    color: hex('#1F2937')
                    font_size: '18sp'
                    bold: True

            # Card Clasificación con color dinámico
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: "65dp"
                padding: [12, 10]
                spacing: "3dp"
                canvas.before:
                    Color:
                        rgba: hex('#EFF6FF')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Label:
                    text: "Clasificación"
                    size_hint_y: None
                    height: "18dp"
                    color: hex('#0369A1')
                    font_size: '11sp'
                    bold: True
                Label:
                    id: value_clasificacion
                    text: "-"
                    size_hint_y: None
                    height: "30dp"
                    color: hex('#1F2937')
                    font_size: '18sp'
                    bold: True

            # Resultado destacado - Surcos
            BoxLayout:
                size_hint_y: None
                height: "80dp"
                padding: [12, 10]
                spacing: "5dp"
                canvas.before:
                    Color:
                        rgba: hex('#FEF2F2')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                
                orientation: 'vertical'
                
                Label:
                    text: "🌾 Surcos Necesarios"
                    size_hint_y: None
                    height: "20dp"
                    color: hex('#991B1B')
                    font_size: '11sp'
                    bold: True
                
                Label:
                    id: surcos_value
                    text: "-"
                    size_hint_y: 1.0
                    color: hex('#DC2626')
                    font_size: '32sp'
                    bold: True

            Widget:
                size_hint_y: None
                height: "15dp"
'''

class CalculadoraRoot(BoxLayout):
    porcentaje_actual = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = CalculoEngine()
        self.calculando = False
        self.debounce_event = None
        
        # Vincular cambios de porcentaje a la UI
        self.bind(porcentaje_actual=self._actualizar_progreso_ui)
        
        # Vincular cambios de texto en inputs para actualizar porcentaje en tiempo real
        self._vincular_inputs()
    
    def _vincular_inputs(self):
        """Vincula los cambios de texto en los inputs"""
        inputs = [
            self.ids.inp_guinea, self.ids.inp_caminadora,
            self.ids.inp_bledo, self.ids.inp_enredadera,
            self.ids.inp_marihuano
        ]
        
        for inp in inputs:
            inp.ids.ti.bind(text=self._en_cambio_input)
    
    def _en_cambio_input(self, instance, value):
        """Se ejecuta cuando cambia el texto de un input"""
        self.actualizar_porcentaje_tiempo_real()
    
    def _actualizar_progreso_ui(self, instance, value):
        """Actualiza la barra de progreso cuando cambia porcentaje_actual"""
        self.ids.progress_bar.value = min(value, 100)
        self.ids.label_porcentaje_progreso.text = f"{value:.1f}%"
    
    def calcular(self):
        """Inicia cálculo con debounce"""
        # Cancelar evento pendiente anterior
        if self.debounce_event:
            self.debounce_event.cancel()
        
        # Programar nuevo cálculo con delay
        self.debounce_event = Clock.schedule_once(
            lambda dt: self._ejecutar_calculo(), 
            Config.DEBOUNCE_DELAY
        )
    
    def actualizar_porcentaje_tiempo_real(self):
        """Actualiza porcentaje en tiempo real (sin calcular todo)"""
        def get_val(widget_id):
            return widget_id.ids.ti.text
        
        guinea = self.engine.validar_entrada(get_val(self.ids.inp_guinea), 100)
        caminadora = self.engine.validar_entrada(get_val(self.ids.inp_caminadora), 100)
        bledo = self.engine.validar_entrada(get_val(self.ids.inp_bledo), 100)
        enredadera = self.engine.validar_entrada(get_val(self.ids.inp_enredadera), 100)
        marihuano = self.engine.validar_entrada(get_val(self.ids.inp_marihuano), 100)
        
        guinea_mod, caminadora_mod = self.engine.calcular_valor_modificado(guinea, caminadora)
        porcentaje = sum([guinea_mod, caminadora_mod, bledo, enredadera, marihuano])
        
        self.porcentaje_actual = porcentaje
        
        # Cambiar color de texto si excede 100
        if porcentaje > 100:
            self.ids.value_porcentaje.color = (1, 0, 0, 1)  # Rojo
        else:
            self.ids.value_porcentaje.color = (31/255, 41/255, 55/255, 1)  # Gris oscuro
    
    def _ejecutar_calculo(self):
        """Ejecuta el cálculo en thread separado"""
        if self.calculando:
            return
        
        self.calculando = True
        thread = threading.Thread(target=self._calcular_background)
        thread.daemon = True
        thread.start()
    
    def _calcular_background(self):
        """Cálculo en background"""
        try:
            def get_val(widget_id):
                return widget_id.ids.ti.text
            
            guinea = self.engine.validar_entrada(get_val(self.ids.inp_guinea), 100)
            caminadora = self.engine.validar_entrada(get_val(self.ids.inp_caminadora), 100)
            bledo = self.engine.validar_entrada(get_val(self.ids.inp_bledo), 100)
            enredadera = self.engine.validar_entrada(get_val(self.ids.inp_enredadera), 100)
            marihuano = self.engine.validar_entrada(get_val(self.ids.inp_marihuano), 100)
            
            largo_text = get_val(self.ids.inp_largo)
            largo_surco = self.engine.validar_entrada(largo_text) if largo_text else 100.0
            
            resultados, error = self.engine.procesar_calculo(
                guinea, caminadora, bledo, enredadera, marihuano, largo_surco
            )
            
            if error:
                Clock.schedule_once(lambda dt: self.mostrar_error(error), 0)
            else:
                Clock.schedule_once(lambda dt: self._actualizar_ui(resultados), 0)
        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.mostrar_error(f"❌ Error: {str(e)}"), 0)
        finally:
            self.calculando = False
    
    def _actualizar_ui(self, resultados):
        """Actualiza UI sin animaciones problemáticas"""
        try:
            # Actualizar porcentaje
            self.ids.value_porcentaje.text = f"{resultados['porcentaje']:.2f}%"
            
            # Actualizar nivel
            self.ids.value_nivel.text = f"Nivel {resultados['nivel']}"
            
            # Actualizar valor formateado
            valor_formateado = f"${resultados['valor_ha']:,.0f}"
            self.ids.value_valor.text = valor_formateado
            
            # Actualizar clasificación con color dinámico
            clasificacion = resultados['clasificacion']
            self.ids.value_clasificacion.text = clasificacion
            color_hex = resultados['color_clasificacion']
            # Convertir hex a RGBA
            from kivy.utils import get_color_from_hex
            color = get_color_from_hex(color_hex)
            self.ids.value_clasificacion.color = color
            
            # Actualizar surcos (sin animación problemática)
            self.ids.surcos_value.text = f"{resultados['surcos']:.2f}"
            
        except Exception as e:
            print(f"Error actualizando UI: {e}")
    
    def reiniciar(self):
        """Reinicia todos los valores"""
        ids_inputs = [
            self.ids.inp_guinea, self.ids.inp_caminadora, 
            self.ids.inp_bledo, self.ids.inp_enredadera, 
            self.ids.inp_marihuano
        ]
        for inp in ids_inputs:
            inp.ids.ti.text = ""
        
        self.ids.inp_largo.ids.ti.text = "100"
        
        # Limpiar resultados
        self.ids.value_porcentaje.text = "0.00%"
        self.ids.value_nivel.text = "-"
        self.ids.value_valor.text = "-"
        self.ids.value_clasificacion.text = "-"
        self.ids.surcos_value.text = "-"
        
        self.porcentaje_actual = 0
    
    def mostrar_error(self, mensaje: str):
        """Muestra popup con mensaje de error"""
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        lbl = Label(text=mensaje, halign='center', size_hint_y=0.6)
        lbl.bind(size=lbl.setter('text_size'))
        content.add_widget(lbl)
        
        btn = Button(text='✓ OK', size_hint_y=0.4, 
                    background_color=UIConstants.CLASIFICACION_COLORES['Alto'])
        btn.background_normal = ''
        content.add_widget(btn)
        
        popup = Popup(title='⚠️ Aviso', content=content, size_hint=(0.85, 0.35))
        btn.bind(on_release=popup.dismiss)
        popup.open()

class PalazonApp(App):
    def build(self):
        self.title = "Calculadora Palazón"
        Builder.load_string(KV_STRING)
        return CalculadoraRoot()

if __name__ == '__main__':
    PalazonApp().run()
