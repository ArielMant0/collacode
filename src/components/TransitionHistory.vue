<template>
    <div>
        <div class="d-flex flex-column align-center pl-4 pr-4" style="width: 100%;">
            <div class="d-flex justify-space-between flex-wrap" style="width: 100%;">
                <div class="d-flex">
                    <v-chip v-for="t in transitions" :key="t.id"
                        density="compact"
                        size="small"
                        class="mr-2"
                        @click="toggle(t.id)"
                        :color="visible.get(t.id) ? 'primary' : 'default'"
                    >{{ nameMap.get(t.id) }}</v-chip>
                </div>
                <div class="d-flex pr-4">
                    <v-btn-toggle v-model="highlightMode" class="ml-1 mr-1" border divided density="comfortable" color="primary" variant="text">
                        <v-tooltip text="highlight changed tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-alert-octagram" value="changes"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight unchanged tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-octagram" value="same"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight moved tag" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-family-tree" value="move"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight split tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-call-split" value="split"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight merged tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-call-merge" value="merge"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight new tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-new-box" value="new"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="highlight deleted tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-delete" value="deleted"/>
                            </template>
                        </v-tooltip>
                    </v-btn-toggle>

                    <v-btn-toggle v-model="linkMode" class="ml-1 mr-1" border divided density="comfortable" mandatory color="primary" variant="text">
                        <v-tooltip text="show links for changed tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-alert-octagram" value="changes"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="show links for unchanged tags" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-octagram" value="same"/>
                            </template>
                        </v-tooltip>
                        <v-tooltip text="show all links" location="top" open-delay="150">
                            <template v-slot:activator="{ props }">
                                <v-btn v-bind="props" icon="mdi-all-inclusive" value="all"/>
                            </template>
                        </v-tooltip>
                    </v-btn-toggle>

                    <v-btn
                        rounded="sm"
                        density="comfortable"
                        @click="reverse = !reverse"
                        :icon="reverse ? 'mdi-sort-variant' : 'mdi-sort-reverse-variant'"/>
                </div>
            </div>

            <div v-for="t in transitions" :key="t.id" style="width: 100%;">
                <TransitionChanges v-if="visible.get(t.id)"
                    :highlight-mode="highlightMode"
                    :link-mode="linkMode"
                    :reverse="reverse"
                    :old-code="t.old_code"
                    :new-code="t.new_code"
                    :max-value="maxValue"
                    :interactions="t.id === app.transitionData.id"
                    @update-max="updateMaxValue"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import TransitionChanges from './TransitionChanges.vue';
    import { storeToRefs } from 'pinia';
    import { onMounted, reactive, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const app = useApp()
    const times = useTimes()
    const { transitions } = storeToRefs(app)

    const reverse = ref(false)
    const maxValue = ref(0)
    const highlightMode = ref("")
    const linkMode = ref("changes")

    const visible = reactive(new Map())
    const nameMap = new Map()

    function updateMaxValue(value) {
        maxValue.value = Math.max(maxValue.value, value)
    }
    function toggle(id) {
        visible.set(id, !visible.get(id))
    }
    function readTrans() {
        nameMap.clear()
        app.transitions.forEach((t, i) => {
            nameMap.set(t.id, `${app.getCodeName(t.old_code)} to ${app.getCodeName(t.new_code)}`)
            if (!visible.has(t.id)) {
                visible.set(t.id, t.id === app.transitionData.id)
            }
        })
    }

    onMounted(readTrans)

    watch(() => Math.max(times.all, times.transitions), readTrans)
</script>