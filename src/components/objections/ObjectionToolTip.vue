<template>
    <ToolTip :x="oX" :y="oY" :data="objection" align="right" :max-width="500">
        <template v-slot:default>
            <div>
                <div class="d-flex justify-space-between text-caption">
                    <div class="d-flex mr-2">
                        <ObjectionIcon :action="objectionData.action" :status="objectionData.status"/>
                        <span class="ml-1">{{ actionStr }}</span>
                    </div>
                    <div class="ml-2"><b>owner:</b> {{ app.getUserName(objectionData.user_id) }}</div>
                </div>
                <div class="mt-1"><b>Explanation</b></div>
                <p v-html="exp"></p>
            </div>
        </template>
    </ToolTip>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import ToolTip from '../ToolTip.vue';
    import { storeToRefs } from 'pinia';
    import ObjectionIcon from './ObjectionIcon.vue';
    import { getActionName, getObjectionStatusName, OBJECTION_STATUS, useApp } from '@/store/app.js';
    import { computed } from 'vue';

    const app = useApp()
    const tt = useTooltip()
    const { objection, objectionData, oX, oY } = storeToRefs(tt)

    const exp = computed(() => {
        if (objectionData.value) {
            return objectionData.value.explanation.replaceAll("\n", "<br/>")
        } 
        return ""  
    })

    const actionStr = computed(() => {
        if (objectionData.value) {
            return getActionName(objectionData.value.action) +
                (objectionData.value.status !== OBJECTION_STATUS.OPEN ?
                    ` [${getObjectionStatusName(objectionData.value.status)}]` :
                    "")

        }
        return ""
    })
</script>