# ==============================================================================
# IMPORTACIONES
# ==============================================================================
# Importamos Lark: Es el motor que analiza el texto (el Parser).
# Importamos Transformer: Es la clase base que nos permite recorrer el árbol 
# sintáctico y convertirlo en datos de Python (el "cerebro" del programa).
from lark import Lark, Transformer

# ==============================================================================
# PARTE 1: LA GRAMÁTICA (Formal Language Theory)
# ==============================================================================
# Definimos la gramática en formato EBNF (Extended Backus-Naur Form).
# Esto le dice al parser CÓMO leer el código.
grammar = """
    // --- REGLA INICIAL (ROOT) ---
    // 'start' es el punto de entrada.
    // 'instruction+' significa que el programa debe tener 1 o más instrucciones.
    // El '+' es un operador de repetición (como en Regex).
    start: instruction+

    // --- REGLAS DE ESTRUCTURA ---
    // Una instrucción puede ser una definición de struct O una asignación.
    // El '|' significa OR (alternativa).
    instruction: struct_def | assignment

    // Definición de un struct (Sintaxis C).
    // Estructura: palabra clave "struct", un nombre (CNAME), llave {, 
    // una lista de campos (field_decl+), llave }, lista de variables, y punto y coma.
    struct_def: "struct" CNAME "{" field_decl+ "}" var_list ";"

    // Declaración de un campo individual (ej: "int a;").
    // Compuesto por un tipo, un nombre y un punto y coma.
    field_decl: type CNAME ";"

    // Lista de variables al final del struct (ej: "x, y").
    // CNAME es obligatoria (la primera variable).
    // ("," CNAME)* significa: una coma y otro nombre, repetido 0 o más veces.
    var_list: CNAME ("," CNAME)*

    // --- REGLA DE ASIGNACIÓN ---
    // Estructura: variable . campo = valor ;
    // Los textos entre comillas (como "." o "=") son literales obligatorios.
    assignment: CNAME "." CNAME "=" value ";"

    // --- TIPOS DE DATOS (Con Alias) ---
    // Usamos '->' (alias) para forzar al parser a crear ramas específicas.
    // Esto evita que Lark oculte estos tokens y facilita procesarlos en Python.
    // Si encuentra "int", llamará a la función 'type_int' del Transformer.
    type: "int"    -> type_int
        | "float"  -> type_float
        | "char"   -> type_char
        | "double" -> type_double
    
    // --- VALORES POSIBLES ---
    // Mapeamos cada tipo de token a una función específica para convertirlo.
    value: INT          -> val_int    // Si es entero -> función val_int
         | FLOAT        -> val_float  // Si es decimal -> función val_float
         | CHAR_LITERAL -> val_char   // Si es caracter -> función val_char

    // --- EXPRESIONES REGULARES (REGEX) ---
    // Definimos qué es un caracter literal (ej: 'c').
    // /[^']/ significa "cualquier cosa que no sea una comilla simple".
    CHAR_LITERAL: "'" /[^']/ "'" 

    // --- IMPORTACIONES DE TOKENS COMUNES ---
    // Lark ya trae regex predefinidas para cosas comunes.
    %import common.CNAME           // Identificadores (letras, _, números)
    %import common.INT             // Números enteros
    %import common.FLOAT           // Números decimales
    %import common.WS              // Espacios en blanco (Whitespace)

    // --- IGNORAR ESPACIOS ---
    // Le decimos al parser que salte los espacios/tabs entre palabras.
    %ignore WS
"""

# ==============================================================================
# PARTE 2: EL TRANSFORMER (Lógica de Procesamiento / Semantic Analysis)
# ==============================================================================
class StructTransformer(Transformer):
    def __init__(self):
        # El constructor se ejecuta al iniciar.
        # Creamos un diccionario vacío para simular la MEMORIA RAM del programa.
        # Estructura: { 'nombre_var': { 'struct_type': '...', 'fields': {...} } }
        self.memory = {}

    def start(self, items):
        # Esta función se llama al final de todo el proceso.
        # Devolvemos la memoria completa para poder imprimirla.
        return self.memory

    # --- MANEJO DE TIPOS (Gracias a los alias '->' en la gramática) ---
    # Estas funciones reciben el token y devuelven un string limpio.
    def type_int(self, items):
        return "int"
    
    def type_float(self, items):
        return "float"
    
    def type_char(self, items):
        return "char"
    
    def type_double(self, items):
        return "double"

    # --- PROCESAMIENTO DE CAMPOS ---
    def field_decl(self, items):
        # Recibimos una lista 'items'.
        # items[0] es el tipo (que viene de las funciones de arriba, ej: "int").
        # items[1] es el nombre del campo (token CNAME, ej: "a").
        
        # Devolvemos un diccionario temporal con la definición del campo.
        return {
            'type': items[0],     
            'name': items[1].value  # .value extrae el texto del token
        }

    # --- DEFINICIÓN DE STRUCTS (Instanciación) ---
    def struct_def(self, items):
        # items[0] es el nombre del struct (ej: "data").
        struct_type_name = items[0].value
        
        # items[-1] es el último elemento: la lista de variables (x, y).
        variables = items[-1]
        
        # items[1:-1] es todo lo que hay en el medio: los campos (field_decl).
        # Usamos slicing de Python para capturarlos todos.
        fields_list = items[1:-1]

        # Bucle para crear cada variable en memoria.
        for var_name in variables:
            # 1. Creamos la entrada en la "RAM" para la variable.
            self.memory[var_name] = {
                'struct_type': struct_type_name,
                'fields': {} # Diccionario vacío para los campos
            }
            
            # 2. Copiamos la "plantilla" de campos a esta variable.
            for field in fields_list:
                # Cada campo inicia en NULL (None en Python).
                self.memory[var_name]['fields'][field['name']] = {
                    'type': field['type'],
                    'value': None 
                }

    # --- LISTA DE VARIABLES ---
    def var_list(self, items):
        # Recibimos tokens sueltos: [Token(x), Token(y)]
        # Usamos una "list comprehension" para extraer solo el texto.
        # Retorna: ['x', 'y']
        return [token.value for token in items]

    # --- ASIGNACIÓN DE VALORES (Semántica y Ejecución) ---
    def assignment(self, items):
        # Extraemos los datos de la instrucción "x.a = 2;"
        var_name = items[0].value   # "x"
        field_name = items[1].value # "a"
        val = items[2]              # 2 (ya convertido a número)

        # --- CHEQUEO SEMÁNTICO (Semantic Checking) ---
        # Antes de escribir, verificamos que la variable exista.
        if var_name in self.memory:
            # Verificamos que el campo exista dentro de esa variable.
            if field_name in self.memory[var_name]['fields']:
                # Si todo es correcto, actualizamos el valor en memoria.
                self.memory[var_name]['fields'][field_name]['value'] = val
            else:
                # Error semántico: Campo no existe.
                print(f"Error: Campo '{field_name}' no existe en '{var_name}'")
        else:
            # Error semántico: Variable no declarada.
            print(f"Error: Variable '{var_name}' no definida")

    # --- CONVERSIÓN DE VALORES (Values) ---
    # Estas funciones convierten el texto del código fuente a tipos reales de Python.
    
    def val_int(self, items):
        return int(items[0]) # Convierte texto "2" a numero entero 2

    def val_float(self, items):
        return float(items[0]) # Convierte texto "2.5" a flotante 2.5

    def val_char(self, items):
        # El token viene con comillas: 'c'
        # Usamos slicing [1:-1] para quitar la primera y última comilla.
        return str(items[0])[1:-1]

# ==============================================================================
# PARTE 3: EJECUCIÓN (PIPELINE)
# ==============================================================================
if __name__ == "__main__":
    # 1. INPUT: Código fuente de prueba (Input String)
    source_code = """
    struct data {
        int a;
        float b;
        char c;
        double d;
        int e;
    } x, y;

    x.a = 2;
    x.c = 'c';
    """
    
    # 2. PARSER GENERATION: Compilamos la gramática.
    # Usamos el algoritmo 'lalr' (Bottom-Up) por eficiencia.
    parser = Lark(grammar, parser='lalr', start='start')

    try:
        # 3. PARSING: Convertimos texto -> Parse Tree (Árbol sintáctico).
        tree = parser.parse(source_code)
        
        # 4. TRANSFORMATION: Instanciamos nuestra clase lógica.
        transformer = StructTransformer()
        
        # 5. EXECUTION: Recorremos el árbol y llenamos la memoria.
        result = transformer.transform(tree)

        # 6. OUTPUT: Imprimimos el resultado formateado como pide el ejercicio.
        print("--- OUTPUT ---")
        
        # Iteramos sobre cada variable en la memoria.
        for var_name, data in result.items():
            print(f"output: struct {var_name}")
            
            # Iteramos sobre los campos de esa variable.
            for f_name, f_data in data['fields'].items():
                val = f_data['value']
                
                # Conversión visual: Si es None, imprimimos "NULL".
                val_str = "NULL" if val is None else str(val)
                
                print(f"   {f_name} type {f_data['type']} value {val_str}")
            
            # Línea vacía para separar structs.
            print("")

    except Exception as e:
        # Si hay errores (sintaxis o código), imprimimos el trazo completo.
        import traceback
        traceback.print_exc()