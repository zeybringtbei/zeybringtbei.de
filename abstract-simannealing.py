from abc import ABC, abstractmethod
import random
from math import exp

class AbstSolution(ABC):

    def __init__(self):
        self.objective = 0
    
    @abstractmethod
    def copy(self):
        pass

class AbstSolutionMnpltr(ABC):

    @abstractmethod
    def genNextSol(self, incsol : AbstSolution) -> AbstSolution:
        """
        Manipulates a given solution, i.e. creates a neighbor or the next best neighbor
        """
        pass

class SimulatedAnnealing:

    def __init__(self, minimize : bool):
        self.minimize = minimize
        self.bestSolution : AbstSolution
    
    def __isBetter(self,solA: AbstSolution, solB : AbstSolution):
        if self.minimize:
            return solA.objective < solB.objective
        
        return solA.objective > solB.objective
    
    def __calcExp(self, nextSol : AbstSolution, incSol : AbstSolution, t : float):
        delta = abs(nextSol.objective-incSol.objective)
        return exp((-(delta))/t) 

    def solve(self, startSol : AbstSolution, solManipulator: AbstSolutionMnpltr, startTemp : int, stopTemp : int, alpha: float):

        self.bestSolution  = startSol.copy()
        incSol = startSol

        t = startTemp

        while(t > stopTemp):

            nextSolution = solManipulator.genNextSol(incSol)

            if self.__isBetter(nextSolution, incSol):  
                incSol = nextSolution
                if self.__isBetter(nextSolution,self.bestSolution):    
                    self.bestSolution = nextSolution.copy()
                    print(self.bestSolution.objective)
            else:
                if random.random() <= self.__calcExp(nextSolution,incSol, t): # Akzeptiere zufällig
                    incSol = nextSolution

            t = alpha * t  


class Tour(AbstSolution):
    def __init__(self):
        super().__init__()
        self.objective = 0 # Länge der Tour
        self.sequence = [] # Sequenz besuchter Orte

    def copy(self) -> AbstSolution:
        # Kopiert die aktuelle Lösung
        s = Tour()
        s.objective = self.objective
        s.sequence = self.sequence[:]
        return s 

class SwapInsert(AbstSolutionMnpltr):

    def __init__(self, dist) -> None:
        super().__init__()
        self.dist = dist
    
    def __swapDelta(self, a : int, b : int, sequence):
        """
        Berechnet das Kostendelta, wenn index a und index b in Sequenz getauscht werden.
        """
        # Macht es einfacher: at ist kleinerer Index
        at = min(a,b)
        bt = max(a,b)

        nodeA = sequence[at]
        aPred = self.__getPred(at,sequence)

        nodeB = sequence[bt]
        bSucc = self.__getSucc(bt,sequence)

        if at != bt-1:
            # Fall 1: a ist nicht direkter Vorgänger von b
            aSucc = self.__getSucc(at,sequence)
            bPred = self.__getPred(bt,sequence)
            delta = -(self.dist[aPred][nodeA] + self.dist[nodeA][aSucc])
            delta -= (self.dist[bPred][nodeB] + self.dist[nodeB][bSucc])
            delta += (self.dist[aPred][nodeB] + self.dist[nodeB][aSucc])
            delta += (self.dist[bPred][nodeA] + self.dist[nodeA][bSucc])
            return delta

        # Fall 2: a ist direkter Vorgänger von b
        delta = -(self.dist[aPred][nodeA] + self.dist[nodeB][bSucc])
        delta -= self.dist[nodeA][nodeB]
        delta += (self.dist[aPred][nodeB] + self.dist[nodeA][bSucc])
        delta += self.dist[nodeB][nodeA]
        return delta

    def __getPred(self, idx,sequence):
        """ Gibt den Vorgänger vom index idx in der Sequenz zurück """
        return 0 if idx == 0 else sequence[idx-1]

    def __getSucc(self,idx,sequence):
        """ Gibt den Nachfolger vom index idx in der Sequenz zurück """
        return 0 if idx == len(sequence)-1 else sequence[idx+1]

    def genNextSol(self, incsol: AbstSolution):
        """Erzeugt eine neue Lösung indem zwei Orte in der Sequenz getauscht werden."""

        # Wähle zwei zufällige Knoten in der Tour
        a,b = random.sample(range(len(incsol.sequence)), 2)

        # Berechne Kostenveränderung
        costDelta = self.__swapDelta(min(a,b),max(a,b),incsol.sequence)

        # Gibt neue Lösung zurück
        newSol = incsol.copy()
        newSol.objective += costDelta
        newSol.sequence[a], newSol.sequence[b] = newSol.sequence[b], newSol.sequence[a]
        return newSol

if __name__ == "__main__":

    # Beispiel mit 10 Orten

    NR_NODES = 100
    dist = [] # Distanzmatrix
    for n in range(NR_NODES+1):
        dist.append([0]*(NR_NODES+1))
        for i in range(0,n):
            dist[i][n] = random.randint(100,200)
            dist[n][i] = dist[i][n]

    # Initialisiere die Klassen
    startSol = Tour()
    solGenerator = SwapInsert(dist=dist)

    # Startlösung [1,2,3,4,...,NR_NODES]
    startSol.sequence = list(range(1,NR_NODES+1))
    startSol.objective = dist[0][1] + dist[NR_NODES][0]
    for i,n in enumerate(startSol.sequence):
        if i==0:
            startSol.objective += dist[0][n]
        elif i==len(startSol.sequence)-1:
            startSol.objective += dist[n][0]
        else:
            startSol.objective += dist[startSol.sequence[i-1]][n]

        
    simAnneal = SimulatedAnnealing(minimize=True)
    simAnneal.solve(startSol,solGenerator,startSol.objective*1.5,1,0.99)