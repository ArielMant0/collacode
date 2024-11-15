<template>
    <v-sheet class="pa-2" max-width="300">
        <v-btn block
            :color="data.selected.size > 0 ? 'primary' : 'default'"
            density="compact"
            :disabled="data.selected.size === 0"
            @click="app.selectByTag()"
            class="mb-4">deselect all</v-btn>
        <v-chip v-for="t in data.tags"
            :key="'tag_'+t.id"
            class="text-caption pt-0 mr-1 mb-1"
            density="compact"
            :color="data.selected.has(t.id) ? 'primary' : 'default'"
            @click="select(t.id)"
            >
            {{ t.name }}
        </v-chip>
    </v-sheet>
</template>

<script setup>

    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app'
    import { reactive, onMounted, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const app = useApp()
    const times = useTimes();

    const data = reactive({
        tags: [],
        selected: new Set()
    });

    function readAll() {
        readTags();
        readSelected();
    }
    function readTags() {
        data.tags = DM.getData("tags", false)
    }
    function readSelected() {
        data.selected = new Set(DM.getFilter("tags", "id"))
    }
    function select(id) {
        app.toggleSelectByTag([id]);
    }

    onMounted(readAll)

    watch(() => times.f_tags, readSelected);
    watch(() => Math.max(times.all, times.tagging, times.tags), readAll, { deep: true })

</script>