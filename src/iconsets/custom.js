import { h } from "vue";
import SetGameIcon from "./SetGameIcon.vue";
import MatchingGameIcon from "./MatchingGameIcon.vue";
import WhoAmIGameIcon from "./WhoAmIGameIcon.vue";
import WhereAmIGameIcon from "./WhereAmIGameIcon.vue";
import TriviaGameIcon from "./TriviaGameIcon.vue";

const nameToComp = {
    "game-set": SetGameIcon,
    "game-matching": MatchingGameIcon,
    "game-trivia": TriviaGameIcon,
    "game-who": WhoAmIGameIcon,
    "game-where": WhereAmIGameIcon,
};

const customIcons = {
    component: props => h(nameToComp[props.icon], props),
};

export { customIcons };