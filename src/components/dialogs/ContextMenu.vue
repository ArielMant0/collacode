<template>
    <Teleport to="body">
        <v-sheet v-if="model"
            class="pa-1"
            :style="{ position: 'absolute', top: y+'px', left: x+'px', 'z-index': 4999 }" border>
            <div ref="wrapper" class="d-flex flex-column text-caption">
                <slot name="text">
                    <div v-for="o in options" class="cursor-pointer pl-1 pr-1 grey-on-hover" @click="select(o)">{{ o[nameAttr] }}</div>
                </slot>
                <div class="mt-2 pl-1 pr-1 cursor-pointer grey-on-hover" @click="close"><i>cancel</i></div>
            </div>
        </v-sheet>
    </Teleport>
</template>

<script setup>
    import { onClickOutside } from '@vueuse/core';
    import { Teleport } from 'vue';

    const emit = defineEmits(["select", "cancel"])

    const model = defineModel()
    const props = defineProps({
        options: {
            type: Array,
            required: true,
        },
        valueAttr: {
            type: String,
            default: "value"
        },
        nameAttr: {
            type: String,
            default: "name"
        },
        returnObject: {
            type: Boolean,
            default: false
        },
        x: {
            type: Number,
            default: 10,
        },
        y: {
            type: Number,
            default: 10,
        },
    })

    const wrapper = ref(null)
    onClickOutside(wrapper, close)

    function select(option) {
        emit("select", props.returnObject ? option : option[props.valueAttr]);
        model.value = false;
    }

    function close() {
        emit("cancel")
        model.value = false;
    }

</script>
