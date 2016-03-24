from dessn.model.node import NodeLatent, NodeTransformation, NodeDiscrete


# class Redshift(NodeLatent):
class Redshift(NodeTransformation):
    def __init__(self, n):
        super(Redshift, self).__init__("redshift", "$z$", group="Redshift")
        self.n = n

    def get_num_latent(self):
        return self.n

    def get_suggestion_requirements(self):
        return ["oredshift"]

    def get_suggestion(self, data):
        return data["oredshift"].tolist()


class Luminosity(NodeLatent):
    def __init__(self, n):
        super(Luminosity, self).__init__("luminosity", "$L$", group="Luminosity")
        self.n = n

    def get_num_latent(self):
        return self.n

    def get_suggestion_requirements(self):
        return ["otype"]

    def get_suggestion(self, data):
        typeIa = data["otype"] == "Ia"
        return typeIa * 10 + (1 - typeIa) * 5.0


# class Type(NodeLatent):
class Type(NodeDiscrete):
    def get_discrete_requirements(self):
        return []

    def get_discrete(self, data):
        return ["Ia", "II"]

    def __init__(self, n):
        super(Type, self).__init__("type", "$T$", group="Type")
        self.n = n

    def get_num_latent(self):
        return self.n

    def get_suggestion_requirements(self):
        return ["otype"]

    def get_suggestion(self, data):
        return data["otype"]
