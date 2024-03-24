<template>
    <div class="d-flex flex-wrap align-center text-caption">
        <v-tooltip v-for="tag in data.tags" :text="tag.description" location="top" open-delay="300">
            <template v-slot:activator="{ props }">
                <v-card v-bind="props"
                    :style="{ 'opacity': !selected || selected[tag.id] ? 1 : 0.5,
                        'border': data.clicked === tag.id ? '2px solid #444' : 'none' }"
                    width="75" height="50"
                    density="compact"
                    class="ma-1 pa-2"
                    @click="onClick(tag)"
                    :color="app.getUserColor(tag.created_by)"
                    >
                    <p class="text-dots">
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
            required: true
        },
        selected: {
            type: Object,
            required: false
        }
    });
    const emit = defineEmits(["click"])

    const data = reactive({ tags: [], clicked: null })

    function readData() {
        data.tags = DM.getData(props.source, false);
    }
    function onClick(tag) {
        data.clicked = data.clicked === tag.id ? null : tag.id;
        emit('click', tag)
    }

    onMounted(readData);

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