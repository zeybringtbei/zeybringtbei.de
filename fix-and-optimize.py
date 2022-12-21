from ortools.linear_solver import pywraplp
from abc import ABC, abstractmethod
from dataclasses import dataclass

class MipModel(ABC):
    def __init__(self,name="mip") -> None:
        self.solver = pywraplp.Solver(name,pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    
    def solve(self):
        self.solver.Solve()
    
    def objective(self):
        return self.solver.Objective().Value()


# 1) Definiere den Solver, den wir verwenden wollen
class Slulsp(MipModel):

    def __init__(self,d, s, l) -> None:

        self.solver = pywraplp.Solver("SLULSP",pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        self.periods = len(d)

        # Variablen
        self.L = self.__initL(self.solver, self.periods)
        self.x = self.__initX(self.solver, self.periods)
        self.y = self.__initY(self.solver, self.periods)

        # Nebenbedingungen
        self.__storageConst(self.solver,self.L, self.x,self.periods,d)
        self.__setupConst(self.solver,self.x, self.y, self.periods)

        # ZF
        self.__addObjective(self.solver,l,self.L,s, self.y)
    
    
    def printSol(self):
        # Ausgabe des Zielfunktionswerts 
        zf_wert = "Zielfunktionswert: {} \n".format(self.solver.Objective().Value())
        print(zf_wert)

        # Lösungsdauer
        dauer = "Lösungsdauer: {} ms".format(self.solver.wall_time())
        print(dauer)

        # Ausgabe der Variablenwert
        for t in range(T):
            print("Wert von {}: {}".format(t,self.x[t].solution_value()))

    def __initL(self, solver, T):
        return [solver.NumVar(0.0, solver.infinity(), "") for _ in range(T)]   # Lagerbestand am Ende von t
    def __initX(self, solver, T):
        return [solver.NumVar(0.0, solver.infinity(), "") for _ in range(T)]   # Produktionsmenge X in t
    def __initY(self, solver, T):
        return [solver.BoolVar("") for _ in range(T)]                          # = 1 wenn in t produziert wird, 0 sonst

    def __storageConst(self,solver,L,x,T,d):
        for t in range(T):
            if(t == 0):
                solver.Add(x[t] - d[t] == L[t])
            else:
                solver.Add(L[t-1] + x[t] - d[t] == L[t])

    def __setupConst(self,solver,x,y,T):
        M = 999999                      # Hinreichend große Zahl
        for t in range(T):
            solver.Add(x[t] <= M*y[t])

    def __addObjective(self,solver,l,L,s,y ):
        solver.Minimize( solver.Sum([l*L[t] + s*y[t] for t in range(T)]) )


@dataclass
class VarValueStorage:
    variable : object
    value : float

class Unfixer(ABC):

    def __init__(self) -> None:
        self.variables_to_unfix = []
    
    @abstractmethod
    def unfix(self,model : MipModel):
        """
        Löst die Fixierung von Variablen. 
        Welche Variablen konkret ausgewählt werden, hängt von der Implementierung ab.
        Wichtig: self.variables_to_unfix leeren.
        """
        pass

    def update_fix_values(self):
        """ Fixiert die neuen Werte der Variablen, die zuvor gelöst wurden.
        """

        # Aktualisiert die neuen Werte der Variablen
        for stored_var in self.variables_to_unfix:
            new_value = stored_var.variable.solution_value()
            stored_var.value = new_value
    
    def refix(self):
        """ Fixiert die Variablen auf die Werte, die sie vor der Unfixierung hatten """
        for stored_var in self.variables_to_unfix:
            prev_value = stored_var.value
            stored_var.variable.SetBounds(prev_value,prev_value)
        
class FixAndOptimize:

    def __init__(self,model : MipModel, unfixer, minimize:bool, iterations=100) -> None:
        self.model = model
        self.unfixer = unfixer
        self.iterations = iterations
        self.minimize = minimize
    
    def __is_better(self,val_a : float, val_b : float):
        if self.minimize:
            return val_a < val_b
        return val_a > val_b
    
    def solve(self):

        # Initiale Lösung bestimmen
        self.bestObjective = self.model.objective()

        # Fix and Optimize für eine gegebene Anzahl Iterationen
        for i in range(self.iterations):

            # Löst Variablenwerte
            self.unfixer.unfix(self.model)

            # Optimiert
            self.model.solve()

            # Updatet die beste bekannte Lösung, falls zutreffend
            if self.__is_better(self.model.objective(), self.bestObjective):
                self.bestObjective = self.model.objective()
                self.unfixer.update_fix_values()
            
            # Fixiert die zuvor gelösten und reoptimierten Variablen erneut
            self.unfixer.refix()

class SlulspUnfixer(Unfixer):

    def __init__(self, lookahead : int) -> None:
        super().__init__()
        self.t_now = 0
        self.lookahead = lookahead

    def unfix(self, model: Slulsp):

        self.variables_to_unfix = []
        
        for pseudo_t in range(self.t_now,self.t_now+self.lookahead+1):
            t = pseudo_t % len(model.y)
            stor = VarValueStorage(model.y[t], model.y[t].lb())
            self.variables_to_unfix.append(stor)
        
        for var in self.variables_to_unfix:
            var.variable.SetBounds(0,1)
        
        self.t_now = self.t_now + 1 % len(model.y)




if __name__ == "__main__":
    # Nachfrage der Perioden
    d = [50,30,20,10,5,50,10,30]    
    # Planungshorizont (= Anzahl Nachfragewerte = 8)
    T = len(d)                      
    # Rüstkostensatz
    s = 50                          
    # Lagerkostensatz
    l = 1                           


    # Startlösung bei der in jeder Periode gerüstet wird
    mip = Slulsp(d,s,l)
    for v in mip.y:
        v.SetBounds(1,1)
    mip.solve()

    # Unfixer mit zwei aufeinanderfolgenden Perioden
    unfixer = SlulspUnfixer(lookahead=2)
    f_and_o = FixAndOptimize(mip, unfixer,True)
    f_and_o.solve()


    mip.solve()
    mip.printSol()




