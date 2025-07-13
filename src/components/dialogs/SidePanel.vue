<template>
    <Teleport to="body">
        <v-card v-if="model"
            ref="el"
            rounded
            elevation="8"
            min-height="95vh"
            :style="{
                position: 'fixed',
                top: '35px',
                left: wL,
                right: wR,
                userSelect: preventUserSelect ? 'none' : 'auto',
                width: width,
                minWidth: minWidth,
                zIndex: zIndex,
                overflowY: 'auto'
            }"
            density="compact">

            <v-card-title>
                <div class="d-flex align-center" style="min-width: 100%;">
                    <v-btn density="compact" size="small" variant="plain" @click="goLeft" :disabled="onLeft" icon="mdi-arrow-left"/>
                    <v-btn density="compact" size="small" variant="plain" @click="goRight" :disabled="!onLeft" icon="mdi-arrow-right"/>
                    <slot name="title"><span class="ml-1">{{ title }}</span></slot>
                    <v-btn style="position: absolute; right: 10px;" icon="mdi-close" color="error" variant="plain" density="compact" @click="close"/>
                </div>
            </v-card-title>

            <v-card-text class="pt-2">
                <slot name="text">
                    {{ text }}
                </slot>
            </v-card-text>
        </v-card>
    </Teleport>

</template>

<script setup>
    import { select } from 'd3';
    import Cookies from 'js-cookie';
    import { useSettings } from '@/store/settings';
    import { computed, onMounted, useTemplateRef, watch } from 'vue';

    const settings = useSettings()

    const model = defineModel()
    const props = defineProps({
        title: { type: String, required: false },
        text: { type: String, required: false },
        width: { type: [Number, String], default: "35%" },
        minWidth: { type: [Number, String], default: "320px" },
        zIndex: { type: Number, default: 2400 },
        preventUserSelect: { type: Boolean, default: false },
    })

    const emit = defineEmits(["close", "show"])

    const el = useTemplateRef("el")
    const wL = ref("20px")
    const wR = ref("auto")
    const onLeft = computed(() => wL.value !== "auto")

    function goLeft() {
        wL.value = "20px"
        wR.value = "auto"
        settings.setPanelSide("left")
    }
    function goRight() {
        wL.value = "auto"
        wR.value = "20px"
        settings.setPanelSide("right")
    }
    function close() {
        model.value = false
        emit("close")
    }
    function read() {
        const side = Cookies.get("panel-side")
        if (side === "left") {
            goLeft()
        } else {
            goRight()
        }
    }
    function getNodeRect() {
        return el.value?.$el.getBoundingClientRect()
    }

    defineExpose({ getNodeRect, goLeft, goRight })

    onMounted(read)

    watch(el, () => {
        if (model.value) {
            select(el.value).raise()
            emit("show")
        }
    })

</script>
