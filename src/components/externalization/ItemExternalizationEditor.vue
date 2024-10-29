<template>
    <div class="d-flex align-start">
        <div style="width: 100%">
            <div style="text-align: center;" class="mb-4 text-caption">
                <p class="mb-1">
                    <i>externalizations are <b>interactions</b> with the game that create or modify visual representations to replace mental simulation or reduce mental load
                    they should not be <b>entirely</b> automated, but at least partially player-driven</i>
                </p>
                <div>
                    <v-btn
                        density="comfortable"
                        class="text-caption mb-2"
                        rounded="sm"
                        :prepend-icon="showExamples ? 'mdi-chevron-up' : 'mdi-chevron-down'"
                        @click="showExamples = !showExamples"
                        color="primary">
                        {{ showExamples ? 'hide' : 'show' }} examples
                    </v-btn>
                </div>

                <div v-if="showExamples" class="d-flex">
                    <span style="width: 33%;">
                        <div><i>strong positive</i></div>
                        <p>
                            <b>Example:</b> players can freely take notes inside the game
                        </p>
                        <p>
                            <b>Explanation:</b> players can use such a feature quite freely to help them offload to external memory or (physically) integrate information to support the sensemaking process
                        </p>
                    </span>
                    <span style="width: 33%;">
                        <div><i>borderline</i></div>
                        <p>
                            <b>Example:</b> players can click on a key to visualize additional information that improves their precision or lets them integrate different pieces of information more effectively (easier or faster)
                        </p>
                        <p>
                            <b>Explanation:</b> low expressiveness together with a high level of automation makes it hard to differentiate between what is just a well-designed feature and what can be considered externalization
                        </p>
                    </span>
                    <span style="width: 33%;">
                        <div><i>strong negative</i></div>
                        <p>
                            <b>Example:</b> players can look up information in a quest log
                        </p>
                        <p>
                            <b>Explanation:</b> while a quest log certainly helps with memory, just looking up information may not help the player, especially if they have no control over what information is actually recorded
                        </p>
                    </span>
                </div>
                <div>
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
            <v-sheet v-for="e in exts" :key="e.id+'_'+time" style="width: 100%;" class="ext-bordered pa-1 mt-2">
                <ExternalizationTile :item="e" @edit="select" allow-edit show-bars/>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import ExternalizationTile from './ExternalizationTile.vue';
    import { useApp } from '@/store/app';
    import { ref, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const time = ref(Date.now())
    const exts = ref(getExts())
    const showExamples = ref(false)

    function select(ext) {
        app.setShowExternalization(ext ? ext.id : null)
    }
    function makeNew() {
        app.setAddExternalization(props.item.id)
    }
    function getExts() {
        if (!app.currentCode) return []
        const array = DM.getDataBy("externalizations", d => d.game_id === props.item.id && d.code_id === app.currentCode)
        array.forEach(e => {
            e.tags.sort((a, b) => {
                if (!a.tag_id || !b.tag_id) return 0;
                const nameA = props.item.allTags.find(d => d.id === a.tag_id).name.toLowerCase();
                const nameB = props.item.allTags.find(d => d.id === b.tag_id).name.toLowerCase();
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            });
        })
        return array
    }

    watch(() => [times.tags, times.datatags, times.externalizations, times.ext_agreements], function() {
        exts.value = getExts()
        time.value = Date.now()
    }, { deep: true });

</script>

<style>
.ext-bordered {
    border: 2px solid white;
    border-radius: 5px;
}
.ext-bordered.selected {
    border-color: #09c293;
}
</style>