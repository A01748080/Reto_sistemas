from mesa import Agent, Model # type: ignore
from mesa.space import SingleGrid # type: ignore
from mesa.time import SimultaneousActivation # type: ignore
from mesa.visualization.modules import CanvasGrid # type: ignore
from mesa.visualization.ModularVisualization import ModularServer # type: ignore
import numpy as np

def generar_celdas_aleatorias(ancho, alto, porcentaje_basura):
    total_celdas = int((porcentaje_basura / 100) * alto * ancho)
    coordenadas = []

    while len(coordenadas) < total_celdas:
        coordenada = (np.random.randint(0, alto), np.random.randint(0, ancho))
        if coordenada not in coordenadas and coordenada != (1, 1):
            coordenadas.append(coordenada)

    return coordenadas

class Basura(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)

class Limpiador(Agent):
    def __init__(self, id, model):
        super().__init__(id, model)
    
    def mover_o_limpiar(self):
        x, y = self.pos
        posibles_movimientos = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]

        nueva_pos = self.random.choice(posibles_movimientos)
        new_x, new_y = nueva_pos

        if 0 <= new_x < self.model.grid.width and 0 <= new_y < self.model.grid.height:
            if self.model.grid.is_cell_empty(nueva_pos):
                self.model.grid.move_agent(self, nueva_pos)
            else: 
                basura_en_celda = [agente for agente in self.model.grid.get_cell_list_contents([nueva_pos]) if isinstance(agente, Basura)]
                if basura_en_celda:
                    self.model.grid.remove_agent(basura_en_celda[0])
                    self.model.grid.move_agent(self, nueva_pos)

    def step(self):
        self.mover_o_limpiar()

class ModeloLimpiadores(Model):
    def __init__(self, ancho, alto, num_limpiadores, porcentaje_basura, tiempo_maximo):
        self.grid = SingleGrid(ancho, alto, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.num_limpiadores = num_limpiadores
        self.contador_limpiadores = 0
        self.tiempo_maximo = tiempo_maximo
        self.tiempo_actual = 0
        self.movimientos_totales = 0
        
        for pos in generar_celdas_aleatorias(ancho, alto, porcentaje_basura):
            basura = Basura(pos, self)
            self.grid.place_agent(basura, pos)
            self.schedule.add(basura)

        self.agregar_limpiador()
    def todas_celdas_limpas(self):
        for contenido_celda, (x, y) in self.grid.coord_iter():
            agentes_en_celda = self.grid.get_cell_list_contents([(x, y)])
            if any(isinstance(agente, Basura) for agente in agentes_en_celda):
                return False
        return True

    def porcentaje_celdas_limpas(self):
        celdas_limpas = sum(1 for contenido_celda, (x, y) in self.grid.coord_iter() if not any(isinstance(agente, Basura) for agente in self.grid.get_cell_list_contents([(x, y)])))
        total_celdas = self.grid.width * self.grid.height
        return (celdas_limpas / total_celdas) * 100

    def step(self):
        self.schedule.step()
        self.agregar_limpiador()
        self.tiempo_actual += 1
        self.movimientos_totales += len([agente for agente in self.schedule.agents if isinstance(agente, Limpiador)])

        if self.todas_celdas_limpas() or self.tiempo_actual >= self.tiempo_maximo:
            self.running = False
            print(f"Tiempo hasta limpiar todas las celdas: {self.tiempo_actual}")
            print(f"Porcentaje de celdas limpias: {self.porcentaje_celdas_limpas()}%")
            print(f"Número total de movimientos: {self.movimientos_totales}")
            return
    def agregar_limpiador(self):
        if self.grid.is_cell_empty((1, 1)) and self.contador_limpiadores < self.num_limpiadores:
            limpiador = Limpiador(self.contador_limpiadores, self)
            self.grid.place_agent(limpiador, (1, 1))
            self.schedule.add(limpiador)
            self.contador_limpiadores += 1

if __name__ == "__main__":
    def representacion_agente(agent):
        if isinstance(agent, Limpiador):
            return {"Shape": "circle", "Filled": "true", "Layer": 0, "Color": "red", "r": 0.5}
        else:
            return {"Shape": "circle", "Filled": "true", "Layer": 0, "Color": "grey", "r": 0.25}

    dimensiones_grid = 24
    num_limpiadores = 200
    porcentaje_basura = 20
    tiempo_maximo = 1000
    grid_visual = CanvasGrid(representacion_agente, dimensiones_grid, dimensiones_grid, 500, 500)
    servidor = ModularServer(ModeloLimpiadores,
                        [grid_visual],
                        "Aspiradora3000",
                        {"ancho": dimensiones_grid, "alto": dimensiones_grid, 
                         "num_limpiadores": num_limpiadores, "porcentaje_basura": porcentaje_basura,
                         "tiempo_maximo": tiempo_maximo})
    servidor.port = 8521
    servidor.launch()
