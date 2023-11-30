from mesa import Agent, Model # type: ignore
from mesa.space import MultiGrid # type: ignore
from mesa.time import SimultaneousActivation # type: ignore
from mesa.visualization.modules import CanvasGrid # type: ignore
from mesa.visualization.ModularVisualization import ModularServer # type: ignore
import numpy as np
import random
from typing import Optional
from math import sqrt

def get_direction(current_pos, next_pos):
    x_curr, y_curr = current_pos
    x_next, y_next = next_pos
    
    if (x_next > x_curr) and (y_next == y_curr):
        return "Right"
    elif (x_next < x_curr) and (y_next == y_curr):
        return "Left"
    elif (x_next == x_curr) and (y_next > y_curr):
        return "Up"
    elif (x_next == x_curr) and (y_next < y_curr):
        return "Down"

def create_neighbor_direction_map(x, y, neighbors):
    current_pos = (x, y)
    neighbor_directions = {}

    for neighbor_pos in neighbors:
        direction = get_direction(current_pos, neighbor_pos)
        neighbor_directions[neighbor_pos] = direction

    return neighbor_directions

# Agente Objeto Edificio:
class Edificio(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.next_state = None

# Agente Objeto Calle:
class Calle(Agent):
    def __init__(self, unique_id, model, street_orientations: list[str]):
        super().__init__(unique_id, model)
        self.next_state = None
        self.street_orientations = street_orientations
        self.position = (0,0)

# Agente Objeto Estacionamiento:
class Estacionamiento(Agent):
    def __init__(self, unique_id, model, idParking):
        super().__init__(unique_id, model)
        self.next_state = None
        self.idParking = idParking
        
# Agente Semáforo:
class Semaforo(Agent):
    def __init__(self, unique_id, model, positions, orientation, initial_state="red"):
        super().__init__(unique_id, model)
        self.positions = positions 
        self.state = initial_state
        self.orientation = orientation
        self.timer = 0
        self.change_threshold = random.randint(5, 15)

    def contar_coches(self):
        coches = 0
        for pos in self.positions:
            x, y = pos
            if self.orientation == "Up":
                casillas_a_revisar = [(x, y-i) for i in range(1, 4)]
            elif self.orientation == "Down":
                casillas_a_revisar = [(x, y+i) for i in range(1, 4)]
            elif self.orientation == "Left":
                casillas_a_revisar = [(x-i, y) for i in range(1, 4)]
            elif self.orientation == "Right":
                casillas_a_revisar = [(x+i, y) for i in range(1, 4)]

            for casilla in casillas_a_revisar:
                if self.model.grid.out_of_bounds(casilla):
                    continue  # Ignora casillas fuera de la grid
                agentes_en_casilla = self.model.grid.get_cell_list_contents(casilla)
                coches += sum(isinstance(agente, Coche) for agente in agentes_en_casilla)

        return coches


# Agente Coche:
class Coche(Agent):
    def __init__(self, unique_id, model, first_parking, destination_parking):
        super().__init__(unique_id, model)
        self.next_state = None
        self.first_parking = first_parking
        self.destination_parking = destination_parking
        self.curr_pos = first_parking
        
    def step(self):
        x, y = self.pos

        print(self.first_parking, 'FIRST')
        print(self.destination_parking, 'DESTINATION')
        successorsList = successors(self, (x, y))

        unique_successors = set(successorsList)
        unique_successors_list = list(unique_successors)
        print("Successors:", unique_successors_list)


        if unique_successors_list:
            unique_sorted_successors = sorted(unique_successors_list, key=lambda s: heuristic(s, self.destination_parking))        
            print("Sorted Successors:", unique_successors_list)
            if random.randint(0, 10) >= 7:
                randomSuccessor = self.random.choice(successorsList)
                unique_sorted_successors = [randomSuccessor]
                
            for sorted_successor in unique_sorted_successors:
                cell = self.model.grid.get_cell_list_contents([sorted_successor])
                parking_objects = [agent for agent in cell if isinstance(agent, Estacionamiento)]
                if goal_test(self, sorted_successor, self.destination_parking):
                    self.model.grid.move_agent(self, sorted_successor)
                    self.model.grid.remove_agent(self)
                    self.model.schedule.remove(self)
                    break
                elif not parking_objects:
                    streetlight_objects = [agent for agent in cell if isinstance(agent, Semaforo)]
                    if streetlight_objects:
                        light_object = streetlight_objects[0]
                        if light_object.state == "green":
                            self.model.grid.move_agent(self, sorted_successor)
                            break
                    else:
                        self.model.grid.move_agent(self, sorted_successor)
                        break

    def render(self):
        return {"First Parking": self.first_parking, "Destination": self.destination_parking}
            

def compare_by_heuristic(self, successor1: tuple[int, int], successor2: tuple[int, int]) -> int:
    heuristic1 = heuristic(successor1, self.destination_parking)
    heuristic2 = heuristic(successor2, self.destination_parking)
    return int(heuristic1 - heuristic2)

def goal_test(self, coor: tuple[int, int], destination_parking: tuple[int, int]) -> bool:
    cell_contents = self.model.grid.get_cell_list_contents([coor])
    parking_objects = [agent for agent in cell_contents if isinstance(agent, Estacionamiento)]
    if parking_objects:
        if destination_parking == coor:
            return True
    return False

def successors(self, coor: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = coor
    neighbours = [(x + dx, y + dy) for dx in [-1, 1] for dy in [0] if 0 <= x + dx <= 23 and 0 <= y + dy <= 23] + [(x + dx, y + dy) for dx in [0] for dy in [-1, 1] if 0 <= x + dx <= 23 and 0 <= y + dy <= 23]
    
    successors: list[tuple[int, int]] = []

    for neighbour in neighbours:
        next_x, next_y = neighbour

        if 0 <= next_x < self.model.grid.width and 0 <= next_y < self.model.grid.height:
            cell_contents = self.model.grid.get_cell_list_contents([(next_x, next_y)])
            street_objects = [agent for agent in cell_contents if isinstance(agent, Calle)]
            car_objects = [agent for agent in cell_contents if isinstance(agent, Coche)]
            building_objects = [agent for agent in cell_contents if isinstance(agent, Edificio)]   
            parking_objects = [agent for agent in cell_contents if isinstance(agent, Estacionamiento)]                     
            # Agente actual
            my_cell_contents = self.model.grid.get_cell_list_contents([(x, y)])
            my_street_objects = [agent for agent in my_cell_contents if isinstance(agent, Calle)]

            # Meter la condición de que si son Parking para que se pueda mandar en la lista de successors
            if parking_objects:
                successors.append(neighbour)

            if not car_objects and not building_objects: # if street_objects and not car_objects and not building_objects:
                    myListOrientations = my_street_objects[0].street_orientations
                    neighbour_directions = create_neighbor_direction_map(x, y, neighbours)
                    for direction in neighbour_directions:
                        if neighbour_directions[direction] in myListOrientations:
                            cell = self.model.grid.get_cell_list_contents([direction])
                            street_objects = [agent for agent in cell if isinstance(agent, Calle)]
                            car_objects = [agent for agent in cell if isinstance(agent, Coche)]
                            if street_objects and not car_objects:
                                successors.append(direction)
    return successors

def heuristic(coor: tuple[int, int], destination_parking: tuple[int, int]) -> float:
    x, y = coor
    goal_x, goal_y = destination_parking

    heuristic_value = sqrt((x - goal_x)**2 + (y - goal_y)**2)

    return heuristic_value

# Creación de coordenadas edificios
def createBuilding(start_position, parkings: list[tuple[int, int]], widthB, heightB):
    coordinates = [(start_position[0] + x, start_position[1] - y) for x in range(widthB) for y in range(heightB) 
                if (start_position[0] + x, start_position[1] - y) not in parkings]
    return coordinates

#Creación de coordenadas calles
def createStreet(start_position, widthS, heightS):
    coordinates = [(start_position[0] + x, start_position[1] - y) for x in range(widthS) for y in range(heightS)]
    return coordinates

def agregarDireccion(coordinate, street_orientations):
  listaRight = [(0, 0), (0, 1), (1, 0), (1, 1), (1, 8), (1, 9), (12,9),(15,9), (15, 16), (15, 17), (14, 16), (14, 17)]
  listaUp = [(22, 0), (23, 0), (22, 1), (23, 1), (22, 22), (22, 23), (23, 22), (23, 23), (14, 1), (15, 1), (14, 22), (15, 22), (14, 23), (15, 23), (14,8),(15,8),(14,11), (5, 11), (6, 11), (5, 10), (6, 10), (18,10), (18, 11), (19, 10), (19, 11)]
  listaDown = [(8, 17), (6, 1), (7, 1), (12, 1), (13, 1), (12, 22), (13, 22), (12, 23), (13, 23), (12, 0), (13, 0), (6, 0), (7, 0), (18, 22), (19, 22), (13,8),(13,11), (6, 8), (6, 9), (7, 8), (7, 9), (9, 22)]
  listaLeft = [(1, 23), (1, 22), (22, 4), (23, 4), (22, 5), (23, 5), (22, 10), (22, 11), (23, 10), (23, 11), (12,11), (12,10),(15,10),(15,11), (15, 13), (15, 4), (15, 5), (12, 16), (12, 17), (13, 16), (13, 17)] 
  if coordinate in listaRight:
      street_orientations.append("Right")
  elif coordinate in listaLeft:
      street_orientations.append("Left")
  elif coordinate in listaUp:
      street_orientations.append("Up")
  elif coordinate in listaDown:
      street_orientations.append("Down")

class CiudadModel(Model):
    def __init__(self, width, height, cars_number):
        self.grid = MultiGrid(width, height, False)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.cars_number = cars_number
        self.id = 0
        self.total_cells = width * height
        self.count_steps = 0
        self.lista_semaforos = []
        
        # Creación de calles
        coorStreet1 = createStreet((0, 23), 2, 24) #Calle izquierda vertical
        
        for coordinate in coorStreet1:
            street = Calle(self.id, self, ['Down'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        coorStreet2 = createStreet((2, 23), 22, 2) #Calle arriba horizontal

        for coordinate in coorStreet2:
            street = Calle(self.id, self, ['Left'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet3 = createStreet((2, 1), 22, 2)  #Calle abajo horizontal

        for coordinate in coorStreet3:
            street = Calle(self.id, self, ['Right'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        coorStreet4 = createStreet((22, 21), 2, 20)  #Calle derceha vertical

        for coordinate in coorStreet4:
            street = Calle(self.id, self, ['Up'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        coorStreet5 = createStreet((2, 17), 10, 2)  #Calle pequeña horizontal izquierda

        for coordinate in coorStreet5:
            street = Calle(self.id, self, ['Left'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet6 = createStreet((5, 15), 2, 4)  #Calle pequeña vertical izquierda

        for coordinate in coorStreet6:
            street = Calle(self.id, self, ['Up'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet7 = createStreet((2, 9), 10, 2)  #Calle pequeña horizontal izquierda abajo 1

        for coordinate in coorStreet7:
            street = Calle(self.id, self, ['Right'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet8 = createStreet((2, 11), 10, 2)  #Calle pequeña horizontal izquierda abajo 2

        for coordinate in coorStreet8:
            street = Calle(self.id, self, ['Left'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet9 = createStreet((6, 7), 2, 6)  #Calle pequeña vertical izquierda abajo

        for coordinate in coorStreet9:
            street = Calle(self.id, self, ['Down'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet10 = createStreet((12, 21), 2, 10)  #Calle central vertical izquierda arriba

        for coordinate in coorStreet10:
            street = Calle(self.id, self, ['Down'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet11 = createStreet((14, 21), 2, 10)  #Calle central vertical derecha arriba

        for coordinate in coorStreet11:
            street = Calle(self.id, self, ['Up'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet12 = createStreet((12, 7), 2, 6)  #Calle central vertical izquierda abajo

        for coordinate in coorStreet12:
            street = Calle(self.id, self, ['Down'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet13 = createStreet((14, 7), 2, 6)  #Calle central vertical derecha abajo

        for coordinate in coorStreet13:
            street = Calle(self.id, self, ['Up'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        coorStreet14 = createStreet((16, 5), 6, 2)  #Calle pequeña horizontal derecha más abajo

        for coordinate in coorStreet14:
            street = Calle(self.id, self, ['Left'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet15 = createStreet((16, 9), 6, 2)  #Calle pequeña horizontal derecha abajo

        for coordinate in coorStreet15:
            street = Calle(self.id, self, ['Right'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet16 = createStreet((16, 11), 6, 2)  #Calle pequeña horizontal derecha central

        for coordinate in coorStreet16:
            street = Calle(self.id, self, ['Left'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet17 = createStreet((16, 17), 6, 2)  #Calle pequeña horizonatl derecha arriba

        for coordinate in coorStreet17:
            street = Calle(self.id, self, ['Right'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
            
        coorStreet18 = createStreet((18, 15), 2, 4)  #Calle vertical derecha central

        for coordinate in coorStreet18:
            street = Calle(self.id, self, ['Up'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        coorStreet19 = createStreet((18, 21), 2, 4)  #Calle vertical derecha arriba

        for coordinate in coorStreet19:
            street = Calle(self.id, self, ['Down'])
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        
        

        # Agregar rotonda
        def crearRotonda(coordinate, direction): 
            street = Calle(self.id, self, direction)
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)
        
        crearRotonda((12, 11), ["Down", "Left"])
        crearRotonda((12, 10), ["Down", "Left"])
        crearRotonda((12, 9), ["Down", "Right"])
        crearRotonda((12, 8), ["Down", "Right"])
        crearRotonda((13, 11), ["Down", "Left"])
        crearRotonda((13, 8), ["Down", "Right"])
        crearRotonda((14, 11), ["Up", "Left"])
        crearRotonda((14, 8), ["Up", "Right"])
        crearRotonda((15, 11), ["Up", "Left"])
        crearRotonda((15, 10), ["Up", "Left"])
        crearRotonda((15, 9), ["Up", "Right"])
        crearRotonda((15, 8), ["Up", "Right"])


        # Crear calle para parking
        def crearCalleParking(coordinate, direction): 
            street = Calle(self.id, self, direction)
            self.id += 1
            self.pos = coordinate
            self.grid.place_agent(street, coordinate)
            self.schedule.add(street)
            agregarDireccion(coordinate, street.street_orientations)

        crearCalleParking((2,20), ["Left"])
        crearCalleParking((6,18), ["Down"])
        crearCalleParking((9,21), ["Up"])
        crearCalleParking((11,19), ["Right"])
        crearCalleParking((2,6), ["Left"])
        crearCalleParking((5,3), ["Right"])
        crearCalleParking((4,13), ["Right"])
        crearCalleParking((8,15), ["Up"])
        crearCalleParking((11,13), ["Right"])
        crearCalleParking((8,3), ["Left"])
        crearCalleParking((17,20), ["Right"])
        crearCalleParking((20,19), ["Left"])
        crearCalleParking((16,13), ["Left"])
        crearCalleParking((17,6), ["Down"])
        crearCalleParking((19,6), ["Down"])
        crearCalleParking((19,3), ["Up"])
        crearCalleParking((21,14), ["Right"])
        
        #Edificios
        parkingsB1 =  [(2, 20), (6, 18), (9, 21), (11, 19)]
        coordBuilding1 = createBuilding((2,21), [], 10, 4)

        parkingsB2 =  [(2, 6), (5,3)]
        coordBuilding2 = createBuilding((2,7), [], 4, 6)

        parkingsB3 =  [(4, 13)]
        coordBuilding3 = createBuilding((2,15), [], 3, 4)
        
        parkingsB4 =  [(8, 15), (11, 13)]
        coordBuilding4 = createBuilding((7,15), [], 5, 4)

        parkingsB5 =  [(8, 3)]
        coordBuilding5 = createBuilding((8,7), [], 4, 6)

        parkingsB6 =  [(17, 20)]
        coordBuilding6 = createBuilding((16,21), [], 2, 4)

        parkingsB7 =  [(20, 19)]
        coordBuilding7 = createBuilding((20,21), [], 2, 4)
        
        parkingsB8 =  [(16, 13)]
        coordBuilding8 = createBuilding((16,15), [], 2, 4)

        parkingsB9 =  [(17, 6), (19,6)]
        coordBuilding9 = createBuilding((16,7), [], 6, 2)
        
        parkingsB10 =  [(19, 3)]
        coordBuilding10 = createBuilding((16,3), [], 6, 2)

        parkingsB11 =  [(21, 14)]
        coordBuilding11 = createBuilding((20,15), [], 2, 4)




        #Glorieta

        parkingsB12 = []
        glorieta = createBuilding((13,10), parkingsB1, 2, 2)

        #Semáforos
        semaforop = []
        semaforo = createBuilding((0,12), semaforop, 2, 1)
        semaforo2 = createBuilding((2,11), semaforop, 1, 2)
        semaforo3 = createBuilding((5,15), semaforop, 2, 1)
        semaforo4 = createBuilding((7,17), semaforop, 1, 2)
        semaforo5 = createBuilding((11,1), semaforop, 1, 2)
        semaforo6 = createBuilding((12,2), semaforop, 2, 1)
        semaforo7 = createBuilding((14,3), semaforop, 2, 1)
        semaforo8 = createBuilding((14,21), semaforop, 2, 1)
        semaforo9 = createBuilding((16,23), semaforop, 1, 2)
        semaforo10 = createBuilding((16,5), semaforop, 1, 2)
        semaforo11 = createBuilding((21,9), semaforop, 1, 2)
        semaforo12 = createBuilding((22,7), semaforop, 2, 1)
        
        
        for coordinate in coordBuilding1:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        contadorParking = 0
        for parkingB1 in parkingsB1:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding2:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB2:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding3:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB3:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding4:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB4:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)

        for coordinate in coordBuilding5:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)
            
        for parkingB1 in parkingsB5:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)

        for coordinate in coordBuilding6:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB6:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding7:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB7:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding8:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB8:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding9:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB9:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
        
        for coordinate in coordBuilding10:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB10:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)

        for coordinate in coordBuilding11:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)

        for parkingB1 in parkingsB11:
            contadorParking += 1
            parking = Estacionamiento(self.id, self, contadorParking)
            self.id += 1
            self.grid.place_agent(parking, parkingB1)
            self.schedule.add(parking)
    
        #Glorieta
        for coordinate in glorieta:
            building = Edificio(self.id, self)
            self.id += 1
            self.grid.place_agent(building, coordinate)
            self.schedule.add(building)
        #Semáforo
    
        building = Semaforo(self.id, self, semaforo12, "Up")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo12:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo11, "Left")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo11:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo10, "Right")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo10:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo9, "Right")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo9:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo8, "Up")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo8:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo7, "Up")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo7:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo6, "Down")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo6:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo5, "Left")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo5:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo4, "Right")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo4:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo3, "Up")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo3:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo2, "Right")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo2:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)

        building = Semaforo(self.id, self, semaforo, "Down")
        self.lista_semaforos.append(building)
        self.id += 1
        for pos in semaforo:
            self.grid.place_agent(building, pos)
        self.schedule.add(building)
    
        # The starting car coordinates are the same as the parking coordinates
        for _ in range(cars_number):
            # starting_parking = self.random.choice(parkingsB1)
            # destination_parking = starting_parking
            # while destination_parking == starting_parking:
            #     destination_parking = self.random.choice(parkingB1)

            parking_lots = [(2, 20), (6, 18), (9, 21), (11, 19), (2, 6), (5, 3), (4, 13), (8, 15), (11, 13), (8, 3),
                            (17, 20), (20, 19), (16, 13), (17, 6), (19, 6), (19, 3), (21, 14)]

            starting_parking = self.random.choice(parking_lots)
            parking_lots.remove(starting_parking)
            destination_parking = self.random.choice(parking_lots)
            car = Coche(self.id, self, starting_parking, destination_parking)
            # car = Coche(self.id, self, (19, 6), (17, 6))
            self.id += 1
            print('Car: ', car.unique_id, 'origin: ', car.first_parking)
            print('Car: ', car.unique_id, 'destination: ', car.destination_parking)
            self.grid.place_agent(car, starting_parking)
            # self.grid.place_agent(car, (19, 6))
            self.schedule.add(car)   
    def comparar_semaforos(self, semaforo1, semaforo2):
        coches1 = semaforo1.contar_coches()
        coches2 = semaforo2.contar_coches()

        if coches1 > coches2:
            semaforo1.state = "green"
            semaforo2.state = "red"
        elif coches1 < coches2:
            semaforo1.state = "red"
            semaforo2.state = "green"
        elif coches1==0 and coches2==0:
            semaforo1.state = "red"
            semaforo2.state = "red"
        else:
            if random.choice([True, False]):
                semaforo1.state = "green"
                semaforo2.state = "red"
            else:
                semaforo1.state = "red"
                semaforo2.state = "green"
    def step(self):
        self.schedule.step()
        self.count_steps += 1
        self.comparar_semaforos(self.lista_semaforos[11], self.lista_semaforos[10])
        self.comparar_semaforos(self.lista_semaforos[9], self.lista_semaforos[8])
        self.comparar_semaforos(self.lista_semaforos[7], self.lista_semaforos[6])
        self.comparar_semaforos(self.lista_semaforos[5], self.lista_semaforos[2])
        self.comparar_semaforos(self.lista_semaforos[3], self.lista_semaforos[4])
        self.comparar_semaforos(self.lista_semaforos[1], self.lista_semaforos[0])

if __name__ == "__main__":   
    def agent_portrayal(agent):
        if isinstance(agent, Coche):
            portrayal = {"Shape": "circle",
                        "Filled": "true",
                        "Layer": 1,
                        "Color": "purple",
                        "r": 1}
        elif isinstance(agent, Edificio):
            portrayal = {"Shape": "rect",
                        "Filled": "true",
                        "Layer": 1,
                        "Color": "blue",
                        "w": 1,
                        "h": 1}
        elif isinstance(agent, Estacionamiento):
            portrayal = {"Shape": "rect",
                        "Filled": "true",
                        "Layer": 1,
                        "Color": "yellow",
                        "w": 1,
                        "h": 1}
        elif isinstance(agent, Calle):
            portrayal = {"Shape": "circle",
                        "Filled": "true",
                        "Layer": 1,
                        "Color": "black",
                        "r": 0.5}
        elif isinstance(agent, Semaforo):
            color = "green" if agent.state == "green" else "red"
            portrayal = {"Shape": "rect",
                        "Filled": "true",
                        "Layer": 1,
                        "Color": color,
                        "w": 1,
                        "h": 1}

        return portrayal

    width = 24
    height = 24
    cars_number = 25
    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)
    server = ModularServer(CiudadModel,
                        [grid],
                        "Ciudad con SMA",
                        {"width":width, "height":height, 
                        "cars_number" : cars_number})
    server.port = 8521 # The default
    server.launch()

    model = server.model