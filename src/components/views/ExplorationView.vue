<template>
    <v-sheet class="pa-0">
    <v-layout>
        <v-sheet class="pa-2" :min-width="expandNavDrawer ? 300 : 60">

            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                :icon="expandNavDrawer ? 'mdi-arrow-left' : 'mdi-arrow-right'"
                block
                density="compact"
                rounded="sm"
                color="secondary"/>

            <v-divider class="mb-2 mt-2"></v-divider>

            <div v-if="!expandNavDrawer" class="d-flex flex-column align-center text-caption">
                <span v-if="transitionData" class="text-caption d-flex flex-column align-center">
                    <b>{{ app.getCodeName(transitionData.old_code) }}</b>
                    to
                    <b>{{ app.getCodeName(transitionData.new_code) }}</b>
                </span>

                <span class="mt-3 mb-1">Games:</span>
                <v-chip density="compact">{{ stats.numGames }}</v-chip>

                <span class="mt-3 mb-1">Tags:</span>
                <v-chip density="compact">{{ stats.numTags }}</v-chip>
                <v-chip v-if="stats.numTagsSel > 0" density="compact" class="mt-1" color="primary">{{ stats.numTagsSel }}</v-chip>
            </div>
            <div v-else>
                <TransitionWidget :initial="activeTransition" :codes="codes" :transitions="transitions"/>
            </div>
        </v-sheet>

        <div style="width: 100%;" class="pa-2">
            <CodingTransition v-if="transitionData"
                :time="myTime"
                :old-code="transitionData.old_code"
                :new-code="transitionData.new_code"
                :include-title="false"
                :edit="false"/>

            <div class="mt-2">
                <GameEvidenceTiles v-if="transitionData" :time="myTime" :code="transition.new_code"/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>

    import { onMounted, reactive, computed, ref, watch } from 'vue';
    import CodingTransition from '@/components/CodingTransition.vue';
    import GameEvidenceTiles from '@/components/evidence/GameEvidenceTiles.vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';

    const app = useApp();
    const settings = useSettings();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        }
    });

    const myTime = ref(props.time);
    const stats = reactive({ numGames: 0, numTagsSel: 0, numTags: 0 })

    const { activeTransition, transitionData, codes, transitions } = storeToRefs(app);
    const { expandNavDrawer } = storeToRefs(settings)

    watch(async () => props.time, function() {
        myTime.value = Date.now();
        stats.numGames = DM.getSize("games", false);
        stats.numTags = DM.getSize("tags", false);
        stats.numTagsSel = DM.hasFilter("tags", "id") ? DM.getSize("tags", true) : 0;
    })

</script>