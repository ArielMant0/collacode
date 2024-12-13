<template>
    <div>
        <div class="d-flex flex-column align-center" style="width: 100%;">
            <div class="d-flex justify-space-between ml-2 mr-2" style="width: 100%;">
                <div class="d-flex">
                    <v-chip v-for="t in transitions" :key="t.id"
                        density="compact"
                        size="small"
                        class="mr-2"
                        @click="toggle(t.id)"
                        :color="visible.get(t.id) ? 'primary' : 'default'"
                    >{{ t.id }}</v-chip>
                </div>
                <div class="d-flex">
                    <v-checkbox-btn v-model="highlight"
                        density="compact"
                        class="mr1"
                        true-icon="mdi-filter"
                        false-icon="mdi-filter-off"/>
                    <v-icon
                        density="compact"
                        class="mr1"
                        @click="reverse = !reverse"
                        :icon="reverse ? 'mdi-sort-variant' : 'mdi-sort-reverse-variant'"/>
                </div>
            </div>

            <div v-for="t in transitions" :key="t.id" style="width: 100%;">
                <TransitionChanges v-if="visible.get(t.id)"
                    :highlight="highlight"
                    :reverse="reverse"
                    :old-code="t.old_code"
                    :new-code="t.new_code"
                    :max-value="maxValue"
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

    const highlight = ref(false)
    const reverse = ref(false)
    const maxValue = ref(0)

    const visible = reactive(new Map())

    function updateMaxValue(value) {
        maxValue.value = Math.max(maxValue.value, value)
    }
    function toggle(id) {
        visible.set(id, !visible.get(id))
    }
    function readTrans() {
        app.transitions.forEach(t => {
            if (!visible.has(t.id)) {
                visible.set(t.id, true)
            }
        })
    }

    onMounted(readTrans)

    watch(() => Math.max(times.all, times.transitions), readTrans)
</script>