from GATHERINGDB.model import IPNode, WorkflowScoreConfig

class ScoringEngine:
    def __init__(
        self,
        crud,  # CRUD_GATHERINGDB instance
        action_scores=None,
        profile_modifiers=None,
        thresholds=None,
        config_model_cls=WorkflowScoreConfig,
    ):
        """
        Recibe CRUD_GATHERINGDB, usa sus métodos para todas las operaciones persistentes.
        """
        self.crud = crud
        self.config_model_cls = config_model_cls

        self._action_scores = action_scores or {
            'scan': 5,
            'lateral_move': 10,
            'exploit': 20,
            'enum': 3,
            'idle': 0,
        }
        self._profile_mod = profile_modifiers or {
            0: 1.0,
            1: 1.3,
            2: 1.7,
        }
        self._thresholds = thresholds or {
            0: 20,
            1: 40,
            2: 65,
        }

    def _find_ipnode(self, ip):
        """Busca IPNode por IP, retorna primero o None"""
        nodes = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
        if nodes and len(nodes):
            return nodes[0]
        return None

    def register_action(self, ip, action_type, profile=None):
        node = self._find_ipnode(ip)
        if not node:
            self.crud.insert_ip(ip, '', '', 0, dao=self.crud.dao)
            node = self._find_ipnode(ip)
        base_score = self._action_scores.get(action_type, 1)
        mod = self._get_profile_mod(node, profile)
        score_add = base_score * mod
        node.score = (getattr(node, "score", 0.0) or 0.0) + score_add
        self.crud.update_ip(node.id, node, dao=self.crud.dao)
        self.on_score_changed(ip, node.score)
        return node.score

    def get_score(self, ip):
        node = self._find_ipnode(ip)
        return getattr(node, "score", 0.0) if node else 0.0

    def set_profile(self, ip, profile):
        node = self._find_ipnode(ip)
        if not node:
            self.crud.insert_ip(ip, '', '', 0, dao=self.crud.dao)
            node = self._find_ipnode(ip)
        node.opsec_flag = profile
        self.crud.update_ip(node.id, node, dao=self.crud.dao)
        # Optional: alert on profile update
        # self.on_profile_changed(ip, profile)

    def reset_score(self, ip):
        node = self._find_ipnode(ip)
        if node:
            node.score = 0.0
            self.crud.update_ip(node.id, node, dao=self.crud.dao)
            self.on_score_changed(ip, node.score)

    def score_threshold(self, ip):
        node = self._find_ipnode(ip)
        profile = getattr(node, "opsec_flag", 1) if node else 1
        return self._thresholds.get(profile, 40)

    def _get_profile_mod(self, node, override_profile=None):
        perfil = override_profile if override_profile is not None else getattr(node, 'opsec_flag', 1)
        return self._profile_mod.get(perfil, 1.3)

    def next_suggestion(self, ip: str) -> str:
        """
        FUTURO: Sugerir acción ideal/menos ruidosa para la IP actual, basado en profile y score.
        Por ahora es un stub, retorna string vacío o warning.
        """
        return "[STUB] Sugerencias OPSEC no implementadas todavía."

    def on_score_changed(self, ip: str, new_score: float):
        """
        Hook opcional: se llama cada vez que un score es actualizado.
        Aquí podés conectar telemetría, alertas, sugerencias, etc.
        (Por defecto no hace nada.)
        """
        pass
