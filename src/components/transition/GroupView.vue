<template>
    <div style="text-align: left;">
        <v-btn color="secondary" block density="compact" @click="group">group</v-btn>
        <div class="mt-2 ml-2 text-caption">
            <div>
                <v-select v-model="parent"
                    :items="otherTags"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    label="group parent's parent"
                    hide-spin-buttons
                    hide-details/>
                <v-text-field v-model="name"
                    label="group parent name"
                    density="compact"
                    class="mb-1 mt-1"
                    hide-details
                    hide-spin-buttons/>
                <v-textarea v-model="desc"
                    label="group parent description"
                    density="compact"
                    class="mb-2"
                    hide-details
                    hide-spin-buttons/>

                <div>group children</div>
                <div v-for="t in selData" :key="t.id" :title="t.pathNames" class="ml-4">
                    <div class="d-flex align-center">
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
    import { groupTags } from '@/use/data-api';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const name = ref("")
    const desc = ref("")
    const parent = ref(null)

    const selData = ref([])
    const otherTags = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        let p = null;
        let minDepth = Number.MAX_SAFE_INTEGER;
        otherTags.value = DM.getDataBy("tags", d => !d._selected)
        selData.value = DM.getData("tags", true)
        selData.value.forEach(d => {
            if (d.path.length < minDepth) {
                minDepth = d.path.length;
                p = d.parent;
            }
        })
        parent.value = p;
    }

    async function group() {
        if (!allowEdit.value) return;

        if (selData.value.length > 0) {

            if (!name.value) {
                return toast.error("missing new tag name")
            }
            if (!desc.value) {
                return toast.error("missing new tag description")
            }

            const names = new Set(DM.getData("tags_name").values())
            if (names.has(name.value)) {
                return toast.error(`tag name ${name.value} already exists`)
            }

            const p = selData.value.find(d => d.id === parent.value);
            if (p) {
                if (p.parent && !selData.value.find(d => d.id === p.parent)) {
                    parent.value = p.parent === -1 ? null : p.parent;
                } else {
                    parent.value = null;
                }
            }

            const parentTag = {
                name: name.value,
                description: desc.value,
                code_id: app.newCode ? app.newCode : app.currentCode,
                created: Date.now(),
                created_by: app.activeUserId,
                is_leaf: false,
                parent: parent.value,
            }

            try {
                await groupTags(parentTag, selData.value.map(d => Object.assign({}, d)))
                toast.success(`grouped ${selData.value.length} tags`)
                resetSelection();
                times.needsReload("tagging")
                name.value = "";
                desc.value = "";
                parent.value = null;
            } catch {
                toast.error("error grouping tags")
            }
        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>