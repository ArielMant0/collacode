<template>
    <div class="d-flex flex-wrap align-center text-caption">
        <v-tooltip v-for="tag in contents.tags" :text="tag.description" location="top" open-delay="300">
            <template v-slot:activator="{ props }">
                <v-card v-bind="props"
                    :style="{ 'opacity': !selected || !tag.id || selected[tag.id] ? 1 : 0.5,
                        'border': highlightClicked && contents && same(contents.clicked, tag) ? '2px solid #444' : 'none' }"
                    :width="width" :height="height"
                    density="compact"
                    class="ma-1 pa-2"
                    @click="onClick(tag)"
                    :color="app.getUserColor(tag.created_by)"
                    >
                    <p>
                        {{ tag.name }}
                    </p>
                </v-card>
            </template>
        </v-tooltip>
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
            default: 50
        },
    });
    const emit = defineEmits(["click"])

    const contents = reactive({ tags: [], clicked: null })

    function same(a, b) {
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
</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
</style>