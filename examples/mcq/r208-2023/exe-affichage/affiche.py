class MaClasse:
    def __init__(self, a, b, l):
        self.a = a
        self.b = b
        self.l = l
    def abra(self, nb):
        self.a = self.a + nb
    def cadabra(self, nb):
        b = self.b + nb
    def wheez(self):
        resultat = 0
        for x in self.l:
            resultat = resultat + x * self.a
        return resultat
    def shazam(self):
        resultat = 0
        for x in self.l:
            if x > self.b:
                resultat = resultat + 1
        return resultat

obj = MaClasse(1, 3, [2, 5, 3])
print(obj.b)
obj.abra(1)
print(obj.a)
print(obj.wheez())
obj.cadabra(1)
print(obj.b)
print(obj.shazam())
autre = obj
autre.abra(1)
print(obj.wheez())
