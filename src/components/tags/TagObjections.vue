<template>
    <v-card v-if="model"
        class="my-window"
        elevation="8"
        rounded
        min-height="95vh"
        :style="{ left: wL, right: wR }"
        density="compact">

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
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, watch } from 'vue';
    import ObjectionTable from '../objections/ObjectionTable.vue';
    import { useSettings } from '@/store/settings';
    import Cookies from 'js-cookie';

    const app = useApp()
    const times = useTimes()
    const settings = useSettings()

    const model = defineModel()
    const props = defineProps({
        id: {
            type: Number,
        },
    })
    const emit = defineEmits(["close"])

    const showAllUsers = ref(app.showAllUsers)
    const name = ref("")

    const wL = ref("20px")
    const wR = ref("auto")

    const excludeHeaders = ["created", "resolution"]

    function goLeft() {
        wL.value = "20px"
        wR.value = "auto"
        settings.setPanelSide("left")
    }
    function goRight() {
        wR.value = "20px"
        wL.value = "auto"
        settings.setPanelSide("right")
    }
    function close() {
        emit("close")
    }

    function readObjections() {
        model.value = props.id !== undefined && props.id !== null
        if (!props.id) {
            name.value = ""
            return
        }

        name.value = DM.getDataItem("tags_name", props.id)

        const side = Cookies.get("panel-side")
        if (side === "left") {
            goLeft()
        } else {
            goRight()
        }
    }

    onMounted(readObjections)

    watch(() => props.id, readObjections)
    watch(() => Math.max(times.datasets, times.objections), readObjections)

</script>

<style scoped>
.my-window {
    position: fixed;
    top: 50px;
    user-select: none;
    width: 32%;
    min-width: 350px;
    height: 95vh;
    z-index: 3;
}
</style>