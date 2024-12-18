<template>
    <div style="text-align: left;">
        <v-number-input v-model="numChildren"
            label="number of children"
            :min="1"
            :step="1"
            class="mb-1"
            control-variant="stacked"
            density="compact"
            @update:model-value="checkChildNames"
            hide-details
            hide-spin-buttons/>
        <v-btn color="primary" block density="compact" @click="add">add</v-btn>
        <div class="ml-2 mt-2 text-caption">
            <div v-for="g in grouped" :key="g.id" :title="g.name">
                {{ g.name }}
                <div v-for="t in g.tags" :key="t.id" :title="t.pathNames" class="ml-4">
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

                    <div v-if="tagNames[t.id]">
                        <div v-for="i in numChildren" class="ml-8" style="width: 100%;">
                            <input v-model="tagNames[t.id][i-1]" type="text" style="font-style: italic; width: 85%;" :placeholder="t.name+' child '+i"/>
                        </div>
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
    import { addTags } from '@/use/utility';
    import { group, range } from 'd3';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const tagNames = reactive({})
    const numChildren = ref(2)

    const grouped = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function checkChildNames() {
        const options = range(0, numChildren.value)
        grouped.value.forEach(t => {
            t.tags.forEach(d => {
                if (!tagNames[d.id]) {
                    tagNames[d.id] = {}
                }
                options.forEach(o => {
                    if (!tagNames[d.id][o]) {
                        tagNames[d.id][o] = d.name + " child " + (o + 1)
                    }
                })
            })
        })
    }

    function update() {
        const selData = DM.getData("tags", true)
        const g = group(selData, d => d.path[0])
        const arr = []
        g.forEach((tags, parent) => arr.push({ id: parent, name: DM.getDataItem("tags_name", parent), tags: tags }))
        grouped.value = arr;
        checkChildNames();
    }

    async function add() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)
        const selData = DM.getData("tags", true)

        const num = numChildren.value;
        const rows = [];
        const now = Date.now();

        if (num > 0 && selData.length > 0) {

            const nameSet = new Set(rows.map(d => d.name))

            selData.forEach(t => {
                for (let i = 0; i < num; ++i) {
                    if (nameSet.has(tagNames[t.id][i])) {
                        return toast.error(`name ${tagNames[t.id][i]} already exists`)
                    }
                    rows.push({
                        name: tagNames[t.id][i],
                        description: "",
                        code_id: app.newCode,
                        parent: t.id,
                        is_leaf: true,
                        created: now,
                        created_by: app.activeUserId
                    })
                }
            })

            try {
                await addTags(rows)
                toast.success("created " + rows.length + " children")
                resetSelection();
                times.needsReload("tags")
            } catch {
                toast.error("error creating " + rows.length + " children")
            }
        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>