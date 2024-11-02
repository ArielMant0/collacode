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
            <ExternalizationGroupTile v-for="g in groups"
                :id="g.id" :key="g.id"
                :item="item"
                allow-edit
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

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const time = ref(Date.now())
    const groups = ref([])
    const showExamples = ref(false)

    function makeNew() {
        app.setAddExternalization(props.item.id)
    }
    function getGroups() {
        if (!app.currentCode) return []
        groups.value = DM.getDataBy("ext_groups", d => d.game_id === props.item.id && d.code_id === app.currentCode)
    }

    onMounted(getGroups)

    watch(() => ([times.externalizations, times.ext_groups]), function() {
        getGroups();
        time.value = Date.now()
    }, { deep: true });

</script>