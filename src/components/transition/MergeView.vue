<template>
    <div style="text-align: left;">
        <v-btn color="secondary" block density="compact" @click="merge">merge</v-btn>
        <div class="mt-2 ml-2 text-caption">
            <div>
                <v-select v-model="parent"
                    :items="otherTags"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    label="new tag parent"
                    hide-spin-buttons
                    hide-details/>
                <v-text-field v-model="name"
                    label="new tag name"
                    density="compact"
                    class="mb-1 mt-1"
                    hide-details
                    hide-spin-buttons/>
                <v-textarea v-model="desc"
                    label="new tag description"
                    density="compact"
                    class="mb-2"
                    @keyup="userDesc = true"
                    hide-details
                    hide-spin-buttons/>

                <div>merged tags</div>
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
                        <span style="text-decoration: line-through;">{{ t.name }}</span>
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
    import { mergeTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { onMounted } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const name = ref("")
    const desc = ref("")
    const parent = ref(null)

    const userDesc = ref(false)

    const selData = ref([])
    const otherTags = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        selData.value = DM.getData("tags", true)
        otherTags.value = DM.getDataBy("tags", d => !d._selected)

        let p = null;
        let minDepth = Number.MAX_SAFE_INTEGER;
        selData.value.forEach(d => {
            if (d.parent && d.path.length - 1 < minDepth) {
                minDepth = d.path.length - 1;
                p = d.parent;
            }
        })
        parent.value = p;

        if (!userDesc.value) {
            desc.value = "merge tags: " + selData.value.map(d => d.name).join(",")
        }
    }

    async function merge() {
        if (!allowEdit.value) return;

        const now = Date.now();

        if (selData.value.length > 0) {

            if (!name.value) {
                return toast.error("missing new tag name")
            }

            if (!desc.value) {
                return toast.error("missing new tag description")
            }

            const nameSet = new Set(DM.getData("tags_name").values())
            selData.value.forEach(d => nameSet.delete(d.name))
            if (nameSet.has(name.value)) {
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

            const obj = {
                name: name.value,
                description: desc.value,
                created: now,
                created_by: app.activeUserId,
                code_id: app.newCode ? app.newCode : app.currentCode,
                parent:  parent.value,
                ids: []
            }
            selData.value.forEach(tag => obj.ids.push(tag.id))

            try {
                await mergeTags(obj)
                toast.success(`merged ${selData.value.length} tags into tag ${name.value}`)
                resetSelection();
                name.value = "";
                desc.value = "";
                parent.value = null;
                userDesc.value = false;
                times.needsReload("tagging")
            } catch {
                toast.error(`error merging ${selData.value.length} tags into tag ${name.value}`)
            }
        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>