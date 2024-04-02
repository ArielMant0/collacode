<template>
    <div class="d-flex flex-wrap text-caption">
            <v-card v-for="tag in contents.tags"
                :style="{ 'border': highlightClicked && contents && same(contents.clicked, tag) ? '1px solid #444' : '1px solid #eee' }"
                :width="width"
                :height="height ? height : 'auto'"
                density="compact"
                class="ma-1 pa-2"
                :elevation="selected && (!tag.id || selected[tag.id]) ? 4 : 0"
                @click="onClick(tag)"
                >
                <v-tooltip :text="tag.description" location="right" open-delay="200">
                    <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" class="float-right cursor-help" density="compact">mdi-information-outline</v-icon>
                    </template>
                </v-tooltip>
                <div class="d-flex flex-column justify-space-between" style="height: 100%">
                    <p style="text-wrap:pretty;">
                        {{ tag.name }}
                    </p>
                    <slot name="actions" :tag="tag"></slot>
                </div>
            </v-card>
    </div>
</template>

<script setup>
    import { reactive, onMounted, watch } from 'vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';

    const app = useApp();
    const props = defineProps({
        source: {
            type: String,
            required: false
        },
        data: {
            type: Array,
            required: false
        },
        selected: {
            type: Object,
            required: false
        },
        highlightClicked: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 75
        },
        height: {
            type: Number,
            default: null
        },
    });
    const emit = defineEmits(["click", "edit", "delete"])

    const contents = reactive({ tags: [], clicked: null })

    function same(a, b) {
        if (!a || !b) return false;
        if (a.id && b.id) {
            return a.id == b.id;
        }
        if (a.name && b.name) {
            return a.name === b.name;
        }
        return false;
    }
    function readData() {
        contents.tags = props.data ? props.data : DM.getData(props.source, false);
    }
    function onClick(tag) {
        contents.clicked = contents.clicked && same(contents.clicked, tag) ? null : tag;
        emit('click', tag)
    }

    onMounted(readData);

    watch(() => props.data, readData, { deep: true })
    watch(() => app.dataLoading._all, readData)
    watch(() => app.dataLoading.transition, readData)
    watch(() => app.dataLoading[props.source], readData)
</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
</style>