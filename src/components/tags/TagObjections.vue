<template>
    <v-dialog :model-value="model"
        class="my-window"
        elevation="8"
        opacity="0"
        min-height="95vh"
        :style="{ left: wL, right: wR }"
        @after-leave="checkClose"
        density="compact">

        <v-card density="compact">
            <v-card-title>
                <v-btn density="compact" size="small" variant="plain" @click="goLeft" :disabled="wL !== 'auto'" icon="mdi-arrow-left"/>
                <v-btn density="compact" size="small" variant="plain" @click="goRight" :disabled="wR !== 'auto'" icon="mdi-arrow-right"/>
                Objections for tag "{{ name }}"
                <v-btn style="float: right;" icon="mdi-close" color="error" variant="plain" density="compact" @click="close"/>
            </v-card-title>
            <v-card-text class="pt-2">

                <div class="d-flex align-center justify-center mb-2">
                    <v-checkbox-btn
                    v-model="showAllUsers"
                    color="primary"
                    density="compact"
                    inline
                    true-icon="mdi-tag"
                    false-icon="mdi-tag-off"
                    :disabled="app.static"/>

                    <span class="ml-1 text-caption">showing {{ showAllUsers ? 'all' : 'your' }} objections</span>
                </div>

                <div style="max-height: 85vh; overflow-y: auto;" class="d-flex flex-wrap">
                    <ObjectionTable v-if="props.id" :tag-id="props.id" :show-all="showAllUsers" :exclude-headers="excludeHeaders"/>
                </div>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, watch } from 'vue';
    import { useTooltip } from '@/store/tooltip';
    import ObjectionTable from '../objections/ObjectionTable.vue';

    const app = useApp()
    const times = useTimes()
    const tt = useTooltip()

    const model = defineModel()
    const props = defineProps({
        id: {
            type: Number,
        },
    })
    const emit = defineEmits(["close"])

    const showAllUsers = ref(false)
    const name = ref("")

    const wL = ref("20px")
    const wR = ref("auto")

    const excludeHeaders = ["created", "resolution"]

    function goLeft() {
        wL.value = "20px"
        wR.value = "auto"
    }
    function goRight() {
        wR.value = "20px"
        wL.value = "auto"
    }
    function close() {
        tt.hideEvidence()
        emit("close")
    }

    function readObjections() {
        model.value = props.id !== undefined && props.id !== null
        if (!props.id) {
            name.value = ""
            return
        }

        name.value = DM.getDataItem("tags_name", props.id)
    }

    function checkClose() {
        if (props.id) {
            emit("close")
        }
    }

    onMounted(readObjections)

    watch(() => props.id, readObjections)
    watch(() => Math.max(times.datasets, times.objections), readObjections)

</script>

<style scoped>
.my-window {
    position: fixed;
    user-select: none;
    width: 45%;
    min-width: 350px;
    height: 95vh;
}
</style>