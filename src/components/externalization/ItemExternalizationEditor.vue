<template>
    <div class="d-flex align-start">
        <div style="width: 100%">
            <div class="mb-4 text-caption">
                <div class="d-flex justify-space-between mb-4">
                    <v-card width="33%" class="text-caption" color="pink-lighten-5">
                        <v-card-title class="text-pink-lighten-2" style="text-align: center;">
                            player data input
                        </v-card-title>
                        <v-card-text>
                            Players must provide some data input that goes into creating the externalization.
                            That can be directly inputting information (e.g., text) or meta-information (e.g., which items should be prioritzed).
                            Simply providing an input action like a mouse click is not sufficient, there must be a connection to problem-related data or features.
                        </v-card-text>
                    </v-card>

                    <v-card width="33%" class="text-caption" color="purple-lighten-5">
                        <v-card-title class="text-purple-lighten-2" style="text-align: center;">
                            extended lifetime
                        </v-card-title>
                        <v-card-text>
                            The created externalization must live for some time (though it can be short) beyond the initial input interaction.
                            This means that information that is only shown during a hover action does not count.
                        </v-card-text>
                    </v-card>

                    <v-card width="33%" class="text-caption" color="indigo-lighten-5">
                        <v-card-title class="text-indigo-lighten-2" style="text-align: center;">
                            mental load reduction
                        </v-card-title>
                        <v-card-text>
                            The created externalization should reduce the player's mental load in relation to the game's challenges.
                            Common ways of reducing mental load is by providing external storage, allowing for simulation (e.g. blueprints) or making information and items more easily accessible.
                            Pure convenience does not fall under this category.
                        </v-card-text>
                    </v-card>
                </div>
                <div v-if="allowEdit" style="text-align: center;">
                    <v-btn
                        color="secondary"
                        rounded="sm"
                        class="text-caption"
                        prepend-icon="mdi-plus"
                        @click="makeNew">
                        add new externalization
                    </v-btn>
                </div>
            </div>
            <ExternalizationGroupTile v-for="g in groups"
                :id="g.id" :key="g.id"
                :item="item"
                :allow-edit="allowEdit"
                class="mb-1"/>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { onMounted, ref, watch } from 'vue';
    import { useTimes } from '@/store/times';
    import ExternalizationGroupTile from './ExternalizationGroupTile.vue';
    import { storeToRefs } from 'pinia';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const { allowEdit } = storeToRefs(app)

    const groups = ref([])

    function makeNew() {
        app.setAddExternalization(props.item.id)
    }
    function getGroups() {
        if (!app.currentCode) return []
        groups.value = DM.getDataBy("meta_groups", d => d.item_id === props.item.id && d.code_id === app.currentCode)
    }

    onMounted(getGroups)

    watch(() => Math.max(times.meta_groups, times.meta_items), getGroups);

</script>