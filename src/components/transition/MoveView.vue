<template>
    <div style="text-align: left;">
        <v-btn color="primary" block density="compact" @click="move">move</v-btn>
        <div class="mt-2 ml-2 text-caption">
            <div>
                how to move tags
                <div v-if="parentData" class="d-flex align-center" @drop="drop" @dragover="allowDrop" :title="parentData.pathNames">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(parent)"/>
                    <v-btn
                        icon="mdi-close"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        class="mr-1"
                        density="compact"
                        color="error"
                        @click="app.toggleSelectByTag([parent])"/>
                    <span>{{ parentData.name }}</span>
                </div>

                <div v-for="t in children" :key="t.id" :title="t.pathNames" class="ml-4">
                    <div class="d-flex align-center" draggable="true" @dragstart="drag(t)">
                        <v-btn
                            icon="mdi-link-variant"
                            size="x-small"
                            rounded="sm"
                            variant="plain"
                            density="compact"
                            class="mr-1"
                            @click="settings.moveToTag(t.id)"/>
                        <v-btn
                            icon="mdi-close"
                            size="x-small"
                            rounded="sm"
                            variant="plain"
                            class="mr-1"
                            density="compact"
                            color="error"
                            @click="app.toggleSelectByTag([t.id])"/>
                        <span>{{ t.name }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { updateTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { ref, computed, watch, onMounted } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(settings)

    const parent = ref(null)
    const parentData = computed(() => selData.value.find(d => d.id === parent.value))
    const selData = ref([])
    const children = computed(() => {
        if (parent.value === null) {
            return selData.value
        }
        return selData.value.filter(d => d.id !== parent.value)
    })

    let dragTag = null;

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        selData.value = DM.getData("tags", true)
        if (selData.value.length === 0) {
            parent.value = null
        } else if (parent.value === null || !selData.value.some(d => d.id === parent.value)) {
            parent.value = selData.value[0].id
        }
    }

    async function move() {
        if (!allowEdit.value) return;

        if (children.value.length > 0 && parent.value !== null) {

            const tags = [];
            children.value.forEach(d => {
                tags.push({
                    id: d.id,
                    name: d.name,
                    description: d.description,
                    parent: parent.value,
                    is_leaf: d.is_leaf
                });
            })

            try {
                await updateTags(tags)
                toast.success("updated " + tags.length + "tag(s)")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error updating " + tags.length + "tag(s)")
            }
        }
    }

    function drag(tag) {
        dragTag = tag;
    }
    function drop() {
        parent.value = dragTag.id;
        dragTag = null;
    }
    function allowDrop(event) { event.preventDefault() }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>