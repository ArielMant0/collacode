<template>
    <v-sheet rounded class="pt-1 pb-1 pl-2 pr-2" :color="color" elevation="1" border @pointerenter="onEnter" @pointerleave="onLeave">
        <div @click="onClick" class="cursor-pointer primary-text-on-hover">
            <div style="text-align: center; position: relative;" class="text-uppercase text-subtitle-1 font-weight-thin">
                <v-icon :icon="model ? 'mdi-pin' : 'mdi-pin-off'" size="small" style="position: absolute; left: 0px; top: 3px"/>
                <slot name="title">
                    {{ title }}
                </slot>
            </div>
        </div>
        <div>
            <slot name="main"></slot>
        </div>
        <v-expand-transition>
            <div v-show="model || hoverModel">
                <slot name="details"></slot>
            </div>
        </v-expand-transition>
    </v-sheet>
</template>

<script setup>
    const model = defineModel({ default: true })
    const props = defineProps({
        title: {
            type: String,
            required: true
        },
        color: {
            type: String,
            default: "surface"
        },
        expandOnClick: {
            type: Boolean,
            default: true
        },
        expandOnHover: {
            type: Boolean,
            default: true
        }
    })

    const hoverModel = ref(false)

    function onClick() {
        if (!props.expandOnClick) return
        model.value = !model.value
    }
    function onEnter() {
        if (!props.expandOnHover) return
        hoverModel.value = true
    }
    function onLeave() {
        if (!props.expandOnHover) return
        hoverModel.value = false
    }

</script>
