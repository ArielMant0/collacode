<template>
    <div class="d-flex justify-start">
        <TagTiles :source="source" @click="onClick" :selected="data.selected" highlight-clicked/>
        <TagWidget :data="data.clicked"/>
    </div>
</template>

<script setup>
    import TagTiles from '@/components/TagTiles.vue';
    import TagWidget from '@/components/TagWidget.vue';
    import { reactive, onMounted } from 'vue';
    import { useApp } from '@/store/app';
    import DM from '@/use/data-manager';

    const app = useApp();
    const props = defineProps({
        source: {
            type: String,
            required: true
        },
    });


    const data = reactive({ clicked: null, selected: {} })

    function onClick(tag) {
        if (data.clicked && data.clicked.id === tag.id) {
            data.clicked = null;
        } else {
            data.clicked = tag;
        }
    }

    function readSelected() {
        const f = DM.getFilter(props.source, "id");
        if (f) {
            const obj = {};
            f.forEach(d => obj[d] = true)
            data.selected = obj;
        } else {
            data.selected = null;
        }
    }

    onMounted(readSelected)

    watch(() => app.selectionTime, readSelected)
</script>