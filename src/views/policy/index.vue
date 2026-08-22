<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <div class="filter-container">
      <el-input
        v-model="listQuery.title"
        placeholder="搜索标题"
        style="width: 200px;"
        class="filter-item"
        clearable
        @keyup.enter.native="handleFilter"
      ></el-input>
      <el-select
        v-model="listQuery.category"
        placeholder="分类筛选"
        clearable
        style="width: 150px"
        class="filter-item"
      >
        <el-option label="法律法规" value="法律法规"></el-option>
        <el-option label="政策措施" value="政策措施"></el-option>
        <el-option label="通知公告" value="通知公告"></el-option>
        <el-option label="工作指引" value="工作指引"></el-option>
      </el-select>
      <el-select
        v-model="listQuery.status"
        placeholder="状态筛选"
        clearable
        style="width: 120px"
        class="filter-item"
      >
        <el-option label="已发布" value="已发布"></el-option>
        <el-option label="草稿" value="草稿"></el-option>
        <el-option label="已撤回" value="已撤回"></el-option>
      </el-select>
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" icon="el-icon-plus" @click="handleAdd">新增政策</el-button>
    </div>

    <!-- 政策列表表格 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="ID" width="80">
        <template slot-scope="scope">{{ scope.row.id }}</template>
      </el-table-column>
      <el-table-column align="center" label="标题" show-overflow-tooltip>
        <template slot-scope="scope">{{ scope.row.title }}</template>
      </el-table-column>
      <el-table-column align="center" label="发布机构" width="150">
        <template slot-scope="scope">{{ scope.row.institution }}</template>
      </el-table-column>
      <el-table-column align="center" label="发布日期" width="120">
        <template slot-scope="scope">{{ scope.row.publish_date }}</template>
      </el-table-column>
      <el-table-column align="center" label="分类" width="120">
        <template slot-scope="scope">
          <el-tag size="small">{{ scope.row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100">
        <template slot-scope="scope">
          <el-tag :type="statusTagType(scope.row.status)" size="small">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="180" fixed="right">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" icon="el-icon-edit" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="danger" size="mini" icon="el-icon-delete" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination v-show="total > 0" :total="total" :page.sync="listQuery.page" :limit.sync="listQuery.limit" @pagination="getList"></pagination>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="650px" :close-on-click-modal="false">
      <el-form ref="policyForm" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入政策标题"></el-input>
        </el-form-item>
        <el-form-item label="发布机构" prop="institution">
          <el-input v-model="form.institution" placeholder="请输入发布机构"></el-input>
        </el-form-item>
        <el-form-item label="发布日期" prop="publish_date">
          <el-date-picker
            v-model="form.publish_date"
            type="date"
            placeholder="选择日期"
            value-format="yyyy-MM-dd"
            style="width: 100%"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
            <el-option label="法律法规" value="法律法规"></el-option>
            <el-option label="政策措施" value="政策措施"></el-option>
            <el-option label="通知公告" value="通知公告"></el-option>
            <el-option label="工作指引" value="工作指引"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="已发布" value="已发布"></el-option>
            <el-option label="草稿" value="草稿"></el-option>
            <el-option label="已撤回" value="已撤回"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="内容摘要">
          <el-input v-model="form.summary" type="textarea" :rows="3" placeholder="请输入内容摘要（可选）"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getPolicyList, createPolicy, updatePolicy, deletePolicy } from '@/api/policy'
import Pagination from '@/components/Pagination'

export default {
  name: 'PolicyList',
  components: { Pagination },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: false,
      listQuery: { page: 1, limit: 10, title: '', category: '', status: '' },
      dialogVisible: false,
      dialogTitle: '新增政策',
      submitLoading: false,
      isEdit: false,
      editId: null,
      form: {
        title: '',
        institution: '',
        publish_date: '',
        category: '',
        status: '草稿',
        summary: ''
      },
      formRules: {
        title: [{ required: true, message: '请输入政策标题', trigger: 'blur' }],
        institution: [{ required: true, message: '请输入发布机构', trigger: 'blur' }],
        publish_date: [{ required: true, message: '请选择发布日期', trigger: 'change' }],
        category: [{ required: true, message: '请选择分类', trigger: 'change' }],
        status: [{ required: true, message: '请选择状态', trigger: 'change' }]
      }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    // 根据状态返回标签类型
    statusTagType(status) {
      const map = { '已发布': 'success', '草稿': 'info', '已撤回': 'danger' }
      return map[status] || 'info'
    },
    // 获取政策列表
    getList() {
      this.listLoading = true
      getPolicyList(this.listQuery).then(response => {
        this.list = response.data.items || []
        this.total = response.data.total || 0
        this.listLoading = false
      }).catch(() => {
        this.listLoading = false
      })
    },
    // 搜索
    handleFilter() {
      this.listQuery.page = 1
      this.getList()
    },
    // 打开新增弹窗
    handleAdd() {
      this.isEdit = false
      this.editId = null
      this.dialogTitle = '新增政策'
      this.form = { title: '', institution: '', publish_date: '', category: '', status: '草稿', summary: '' }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.policyForm && this.$refs.policyForm.clearValidate()
      })
    },
    // 打开编辑弹窗
    handleEdit(row) {
      this.isEdit = true
      this.editId = row.id
      this.dialogTitle = '编辑政策'
      this.form = {
        title: row.title,
        institution: row.institution,
        publish_date: row.publish_date,
        category: row.category,
        status: row.status,
        summary: row.summary || ''
      }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.policyForm && this.$refs.policyForm.clearValidate()
      })
    },
    // 提交表单
    handleSubmit() {
      this.$refs.policyForm.validate(valid => {
        if (!valid) return
        this.submitLoading = true
        const action = this.isEdit
          ? updatePolicy(this.editId, this.form)
          : createPolicy(this.form)
        action.then(() => {
          this.$message.success(this.isEdit ? '修改成功' : '新增成功')
          this.dialogVisible = false
          this.getList()
          this.submitLoading = false
        }).catch(() => {
          this.submitLoading = false
        })
      })
    },
    // 删除政策
    handleDelete(id) {
      this.$confirm('确认删除该政策文件？此操作不可恢复。', '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        deletePolicy(id).then(() => {
          this.$message.success('删除成功')
          this.getList()
        })
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.filter-container { padding-bottom: 20px; }
.filter-item { margin-right: 10px; }
</style>
