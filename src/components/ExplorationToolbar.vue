<template>
    <v-sheet class="d-flex justify-center mb-2">
        <v-btn-toggle v-model="tagFilter" color="primary" density="compact" rounded="sm" elevation="2" divided mandatory variant="text" class="mr-4" @update:model-value="filterByTags">

            <v-tooltip text="cluster layout with leaves on the same level" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="all">all</v-btn>
                </template>
            </v-tooltip>

            <v-tooltip text="show tags related to externalization" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="ext">ext</v-btn>
                </template>
            </v-tooltip>

            <v-tooltip text="show tags related to visualization" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="vis">vis</v-btn>
                </template>
            </v-tooltip>

            <v-tooltip text="show other tags" location="bottom">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" class="pl-4 pr-4" value="other">other</v-btn>
                </template>
            </v-tooltip>
        </v-btn-toggle>
    </v-sheet>
</template>

<script setup>
    import { ref } from 'vue';
    import DM from '@/use/data-manager'
    import { useApp } from '@/store/app';

    const app = useApp();
    const tagFilter = ref("all");

    function filterByTags() {
        const tags = DM.getData("tags", false);

        let ids;

        switch(tagFilter.value) {
            case "ext":
                ids = tags
                    .filter(d => d.name.match(/^ext\:/) !== null)
                    .map(d => d.id)
                break;
            case "vis":
                ids = tags
                    .filter(d => d.name.match(/^vis\:/) !== null)
                    .map(d => d.id)
                break;
            case "other":
                ids = tags
                    .filter(d => d.name.match(/^vis\:/) === null && d.name.match(/^ext\:/) === null)
                    .map(d => d.id)
                break;
        }

        app.selectByTag(ids);
    }
</script>