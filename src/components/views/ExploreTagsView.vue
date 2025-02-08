<template>
    <v-sheet class="pa-0">
        <div ref="el" style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">

                <ItemHistogram
                    :attributes="allItemAttr"
                    :width="Math.max(600, Math.min(900, width-10))"/>

                <div class="d-flex align-start">
                    <TagCorrelation/>
                    <TagUserMatrix v-if="app.showAllUsers" :size="150" class="ml-8"/>
                </div>

            </div>
        </div>
    </v-sheet>
</template>

<script setup>

    import { max } from 'd3';
    import ItemHistogram from '../items/ItemHistogram.vue';
    import TagCorrelation from '../tags/TagCorrelation.vue';

    import { computed, ref, watch } from 'vue';
    import { useElementSize } from '@vueuse/core';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import TagUserMatrix from '../tags/TagUserMatrix.vue';

    const app = useApp();
    const settings = useSettings();

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })
    const el = ref(null)
    const { width } = useElementSize(el)
    const active = computed(() => settings.activeTab === "explore_tags")

    const myTime = ref(Date.now());

    const itemAttrs = [
        { title: "tags per item", key: "numTags", aggregate: true },
        { title: "evidence per item", key: "numEvidence", aggregate: true },
        { title: "meta items per item", key: "numMeta", aggregate: true },
        { title: "expertise ratings", key: "expertise", value: d => getExpValue(d), min: 0, max: 3, labels: { 0: "none", 1: "basic", 2: "knowledgeable", 3: "expert" } },
    ]

    const allItemAttr = computed(() => {
        if (!app.schema) return itemAttrs
        return itemAttrs.concat(app.schema.columns
            .filter(d => d.type !== "string")
            .map(d => {
                const obj = Object.assign({}, d)
                obj.title = d.name.replaceAll("_", " ");
                obj.key = d.name;
                obj.aggregate = true;
                return obj
            }))
    })

    function getExpValue(game) {
        if (app.showAllUsers) {
            return max(app.users.map(u => {
                const r = game.expertise.find(d => d.user_id === u.id)
                return r ? r.value : 0
            }))
        }
        const r = game.expertise.find(d => d.user_id === app.activeUserId)
        return r ? r.value : 0
    }

    watch(active, (now) => { if (now) myTime.value = Date.now() })

</script>