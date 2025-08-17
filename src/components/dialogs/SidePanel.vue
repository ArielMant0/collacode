<template>
    <v-dialog v-model="model"
        attach="body"
        :scrim="false"
        :style="{
            position: 'fixed',
            top: '-10px',
            left: wL,
            right: wR,
            width: width,
            minWidth: minWidth,
            maxHeight: '100vh',
            zIndex: zIndex
        }">
        <v-card
            ref="el"
            rounded
            style="overflow-y: auto; max-height: 98vh;"
            min-height="97vh"
            density="compact">

            <v-card-title>
                <div class="d-flex align-center" style="min-width: 100%; max-width: 100%;">
                    <v-btn density="compact" size="small" variant="plain" @click="goLeft" :disabled="onLeft" icon="mdi-arrow-left"/>
                    <v-btn density="compact" size="small" variant="plain" @click="goRight" :disabled="!onLeft" icon="mdi-arrow-right"/>
                    <slot name="title"><span class="ml-1 text-dots">{{ title }}</span></slot>
                    <v-btn
                        style="position: absolute; right: 10px;"
                        :style="{ backgroundColor: lightMode ? 'white' : 'black' }"
                        class="bordered-grey-light-thin"
                        rounded="sm"
                        icon="mdi-close"
                        color="error"
                        variant="text"
                        density="compact"
                        @click="close"/>
                </div>
            </v-card-title>

            <v-card-text class="pt-2">
                <slot name="text">
                    {{ text }}
                </slot>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
    import { select } from 'd3';
    import Cookies from 'js-cookie';
    import { useSettings } from '@/store/settings';
    import { computed, onMounted, useTemplateRef, watch } from 'vue';
    import { storeToRefs } from 'pinia';

    const settings = useSettings()
    const { lightMode } = storeToRefs(settings)

    const model = defineModel()
    const props = defineProps({
        title: { type: String, required: false },
        text: { type: String, required: false },
        width: { type: [Number, String], default: "35vw" },
        minWidth: { type: [Number, String], default: "320px" },
        zIndex: { type: Number, default: 3400 },
        preventUserSelect: { type: Boolean, default: false },
    })

    const emit = defineEmits(["close", "show"])

    const el = useTemplateRef("el")
    const wL = ref("0px")
    const wR = ref("auto")
    const onLeft = computed(() => wL.value !== "auto")

    function goLeft() {
        wL.value = "0px"
        wR.value = "auto"
        settings.setPanelSide("left")
    }
    function goRight() {
        wL.value = "auto"
        wR.value = "0px"
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
            setTimeout(() => emit("show"), 150)
        }
    })

</script>
