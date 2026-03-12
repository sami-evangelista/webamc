class Switch:
    def ________(self, num, nb):
        self.nom = "S" + num
        self.ports = nb + 8
        self.allume = ________
    def ajouter_ports(self, nb):
        """Ajouter nb ports au switch."""
        ________
    def ________(self):
        return self.nom + " (" + str(self.ports) + " ports)"
    def ________(self, autre):
        return self.ports > autre.ports

s1 = Switch(________)
print(s1)
if not s1.allume:
    s1.allume = True
print(s1.allume)
________
print(s1)
s2 = Switch(________)
if s1 < s2:
    print("S1 < S2")
