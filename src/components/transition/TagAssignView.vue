<template>
    <div class="text-caption" style="text-align: left;">
        <div class="d-flex justify-space-between mb-2">
            <v-btn style="width: 49%" density="compact" @click="add"
                :disabled="existing !== undefined"
                :color="existing === undefined ? 'secondary' : 'default'"
                >
                add
            </v-btn>
            <v-btn style="width: 49%" density="compact" @click="remove"
                :disabled="existing === undefined"
                :color="existing !== undefined ? 'error' : 'default'"
                >
                delete
            </v-btn>
        </div>
        <div class="d-flex justify-space-between mb-4">
            <v-btn density="compact" @click="update"
                block
                :disabled="forOld.length !== 1 || forNew.length !== 1"
                :color="forOld.length === 1 && forNew.length === 1 ? 'primary' : 'default'"
                >
                update existing
            </v-btn>
        </div>
        <div class="ml-2">
            <div>Old Tag</div>
            <div v-if="transOld >= 0" class="d-flex align-center">
                <v-btn
                    icon="mdi-link-variant"
                    size="x-small"
                    rounded="sm"
                    variant="plain"
                    density="compact"
                    class="mr-1"
                    @click="settings.moveToTag(transOld)"/>
                <v-btn
                    icon="mdi-close"
                    size="x-small"
                    rounded="sm"
                    variant="plain"
                    class="mr-1"
                    density="compact"
                    color="error"
                    @click="DM.toggleFilter('tags_old', transOld)"/>
                <span>{{ oldTagName }}</span>
            </div>

            <div class="mt-1">New Tag</div>
            <div v-if="transNew >= 0" class="d-flex align-center">
                <v-btn
                    icon="mdi-link-variant"
                    size="x-small"
                    rounded="sm"
                    variant="plain"
                    density="compact"
                    class="mr-1"
                    @click="settings.moveToTag(transNew)"/>
                <v-btn
                    icon="mdi-close"
                    size="x-small"
                    rounded="sm"
                    variant="plain"
                    class="mr-1"
                    density="compact"
                    color="error"
                    @click="app.toggleSelectByTag([transNew])"/>
                <span>{{ newTagName }}</span>
            </div>
            <div v-else>{{ "<none>" }}</div>

            <v-divider class="mt-2 mb-2"></v-divider>

            <div>Existing Assignments (old)</div>
            <div v-if="forOld.length > 0">
                <div v-for="t in forOld" :key="t.new_tag" class="d-flex align-center">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(t.new_tag)"/>
                    <span>{{ t.name }}</span>
                </div>
            </div>
            <div v-else>{{ "<none>" }}</div>

            <div class="mt-1">Existing Assignments (new)</div>
            <div v-if="forNew.length > 0">
                <div v-for="t in forNew" :key="t.old_tag" class="d-flex align-center">
                    <v-btn
                        icon="mdi-link-variant"
                        size="x-small"
                        rounded="sm"
                        variant="plain"
                        density="compact"
                        class="mr-1"
                        @click="settings.moveToTag(t.old_tag)"/>
                    <span>{{ t.name }}</span>
                </div>
            </div>
            <div v-else>{{ "<none>" }}</div>
        </div>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { addTagAssignments, deleteTagAssignments, updateTagAssignments } from '@/use/data-api';
    import { storeToRefs } from 'pinia';
    import { computed } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()
    const settings = useSettings()

    const { transOld, transNew } = storeToRefs(settings)

    const existing = computed(() => {
        if (transOld.value < 0 || transNew.value < 0) {
            return undefined;
        }
        return DM.find("tag_assignments", d => d.old_tag === transOld.value && d.new_tag === transNew.value)
    })
    const forOld = computed(() => {
        if (transOld.value < 0) {
            return [];
        }
        const res = DM.getDataBy("tag_assignments", d => d.old_code === app.oldCode && d.old_tag === transOld.value)
        .map(d => {
                const obj = Object.assign({}, d)
                obj.name = DM.getDataItem("tags_name", d.new_tag)
                return obj
            })

        return res
    })
    const forNew = computed(() => {
        if (transNew.value < 0) {
            return [];
        }
        const res = DM.getDataBy("tag_assignments", d => d.new_code === app.newCode && d.new_tag === transNew.value)
            .map(d => {
                const obj = Object.assign({}, d)
                obj.name = DM.getDataItem("tags_old_name", d.old_tag)
                return obj
            })

        return res
    })
    const oldTagName = computed(() => transOld.value >= 0 ? DM.getDataItem("tags_old", transOld.value).name : "")
    const newTagName = computed(() => transNew.value >= 0 ? DM.getDataItem("tags", transNew.value).name : "")

    function reset() {
        DM.removeFilter("tags_old")
        app.selectByTag([])
        transOld.value = -1;
        transNew.value = -1;
    }

    async function add() {
        if (transOld.value >= 0 && transNew.value >= 0 && !existing.value) {
            try {
                await addTagAssignments([{
                    old_code: app.oldCode,
                    new_code: app.newCode,
                    old_tag: transOld.value,
                    new_tag: transNew.value,
                    description: "ADDED",
                    created: Date.now()
                }])
                toast.success("added new tag assignment")
                reset()
                times.needsReload("tag_assignments")
            } catch {
                toast.error("error adding new tag assignment")
            }
        }
    }

    async function update() {
        if (transOld.value >= 0 && transNew.value >= 0 && forOld.value.length === 1 && forNew.value.length === 1) {
            try {
                const obj1 = Object.assign({}, forOld.value[0])
                obj1.new_tag = transNew.value
                obj1.description = "UPDATED"
                const obj2 = Object.assign({}, forNew.value[0])
                obj2.old_tag = transOld.value
                obj2.description = "UPDATED"

                await updateTagAssignments([obj1, obj2])
                toast.success("updated tag assignments")
                reset()
                times.needsReload("tag_assignments")
            } catch {
                toast.error("error updating tag assignments")
            }
        }
    }

    async function remove() {
        if (transOld.value >= 0 && transNew.value >= 0 && existing.value) {
            try {
                await deleteTagAssignments([existing.value.id])
                toast.success("removed tag assignment")
                reset()
                times.needsReload("tag_assignments")
            } catch {
                toast.error("error removing tag assignment")
            }
        }
    }
</script>