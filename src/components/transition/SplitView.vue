<template>
    <div style="text-align: left;">
        <v-number-input v-model="numChildren"
            label="number of children"
            :min="2"
            :step="1"
            class="mb-1"
            control-variant="stacked"
            density="compact"
            @update:model-value="checkChildNames"
            hide-details
            hide-spin-buttons/>

        <v-btn color="secondary" rounded="sm" block density="compact" @click="split">split</v-btn>

        <div v-if="tag" class="mt-2 ml-2 text-caption">
            <div v-if="tag.parentName">{{ tag.parentName }}</div>
            <div class="ml-4 d-flex align-center">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(tag.id)"/>
                    <v-btn
                        icon="mdi-close"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        class="mr-1"
                        density="compact"
                        color="error"
                        @click="app.toggleSelectByTag([tag.id])"/>
                <span style="text-decoration: line-through;">{{ tag.name }}</span>
            </div>
            <div v-for="i in numChildren" class="ml-4" style="width: 100%;">
                <input v-model="tagNames[i-1]" type="text" style="font-style: italic; width: 85%;" :placeholder="'tag '+i"/>
            </div>

        </div>

        <div v-if="tag" class="text-caption">
            <v-divider class="mt-2 mb-2"></v-divider>
            <v-btn color="primary" rounded="sm" block density="compact" class="mb-2" :disabled="items.length == 0" @click="openAssignment">adjust assignments</v-btn>

            <div v-for="i in numChildren" class="ml-4" style="width: 100%;">
                <b>{{ tagNames[i-1] }}</b>: {{ numAssigned.get(i-1) }} item(s)
            </div>
        </div>

        <v-dialog v-model="dialog" min-width="85%" min-height="50%" max-height="95%">
            <v-card max-height="95%" style="overflow-y: auto;">
                <v-card-title>Assign {{ app.itemName }}s to tags</v-card-title>
                <v-card-text>
                    <div class="text-caption mb-2" style="text-align: center;">
                        <i>drag images to change the assignment</i>
                    </div>
                    <AssignmentPuzzle
                        :options="tagNamesArray"
                        :items="items"
                        :initial="initialAssignment"
                        @update="updateAssignment"
                        :image-width="120"
                        :image-height="60"
                        item-image="teaser"
                        image-prefix="teaser/"/>
                </v-card-text>
                <v-card-actions>
                    <v-btn block @click="closeAssignment">close</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { splitTags } from '@/use/data-api';
    import { range } from 'd3';
    import { storeToRefs } from 'pinia';
    import { ref, onMounted, watch, reactive, computed } from 'vue';
    import { useToast } from 'vue-toastification';
    import AssignmentPuzzle from '../AssignmentPuzzle.vue';
    import { useSettings } from '@/store/settings';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const tagNames = reactive({})
    const tagNamesArray = computed(() => Object.values(tagNames))
    const numChildren = ref(2)

    const items = ref([])
    const dialog = ref(false)

    const tag = ref(null)
    const initialAssignment = reactive(new Map())
    const numAssigned = reactive(new Map())
    let assignments = new Map();

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function checkChildNames(reset=false) {
        const options = range(0, numChildren.value)
        options.forEach(o => {
            if (!tagNames[o] || reset === true) {
                tagNames[o] = "tag " + (o + 1)
            }
        })
        const keys = Object.keys(tagNames)
        for (let i = options.length; i < keys.length; ++i) {
            delete tagNames[i]
        }
        checkAssigned()
    }

    function checkAssigned() {
        const reset = items.value.length !== DM.getSize("items", true)
        const tagSet = DM.getSelectedIds("tags")
        items.value = DM.getDataBy("items", d => d.allTags.some(dd => tagSet.has(dd.id)))

        if (reset || assignments.size === 0) {
            assignments.clear()
            items.value.forEach(d => assignments.set(d.id, 0))
        } else {
            const sel = DM.getSelectedIds("items")
            const current = Array.from(assignments.keys())
            // remove those that no longer exist
            current.forEach(d => {
                if (!sel.has(d)) {
                    assignments.delete(d)
                }
            })
            // add those missing
            items.value.forEach(d => {
                if (!assignments.has(d.id)) {
                    assignments.set(d.id, 0)
                }
            })
        }

        numAssigned.clear()
        tagNamesArray.value.forEach((_, i) => numAssigned.set(i, 0))

        const needsReset = new Set()
        assignments.forEach((v, k) => {
            if (v >= tagNamesArray.value.length) {
                needsReset.add(k)
                numAssigned.set(0, numAssigned.get(0) + 1)
            } else {
                numAssigned.set(v, numAssigned.get(v) + 1)
            }
        })

        if (needsReset.size > 0) {
            needsReset.forEach(d => assignments.set(d, 0))
            initialAssignment.clear()
            assignments.forEach((v, k) => initialAssignment.set(k, v))
        }
    }

    function update() {
        const selData = DM.getData("tags", true)
        if (selData.length === 0) {
            tag.value = null;
            checkChildNames(true)
        } else if (tag.value === null || selData[0].id !== tag.value.id) {
            tag.value = selData[0]
            tag.value.parentName = tag.value.parent ? DM.getDataItem("tags_name", tag.value.parent) : null
            checkChildNames(true)
        }
        checkAssigned()
    }

    async function split() {
        if (!allowEdit.value) return;
        const num = numChildren.value;
        const now = Date.now();

        if (num > 0 && tag.value !== null) {

            const names = [];
            const nameSet = new Set(DM.getData("tags_name").values())
            for (let i = 0; i < num; ++i) {
                if (nameSet.has(tagNames[i])) {
                    return toast.error(`name ${tagNames[i]} already exists`)
                }
                names.push(tagNames[i])
            }

            try {
                const amap = []
                assignments.forEach((v, k) => amap.push({ id: +k, tag: names[v] }))
                await splitTags([{
                    id: tag.value.id,
                    names: names,
                    assignments: amap,
                    created_by: app.activeUserId,
                    created: now
                }])
                toast.success("split tag into " + names.length + " children")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error splitting tag")
            }
        }
    }

    function openAssignment() {
        initialAssignment.clear()
        if (assignments.size > 0) {
            assignments.forEach((v, k) => initialAssignment.set(k, v))
        }
        dialog.value = true;
    }
    function updateAssignment(data) {
        assignments = data;
        numAssigned.clear()
        data.forEach((v, _) => numAssigned.set(v, (numAssigned.get(v) || 0) + 1))
    }
    function closeAssignment() {
        dialog.value = false;
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>