<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <div class="filter-container">
      <el-input
        v-model="listQuery.name"
        placeholder="搜索姓名"
        style="width: 200px;"
        class="filter-item"
        clearable
        @keyup.enter.native="handleFilter"
      ></el-input>
      <el-select
        v-model="listQuery.region"
        placeholder="地区筛选"
        clearable
        style="width: 150px"
        class="filter-item"
      >
        <el-option label="香港" value="香港"></el-option>
        <el-option label="澳门" value="澳门"></el-option>
        <el-option label="台湾" value="台湾"></el-option>
        <el-option label="华侨" value="华侨"></el-option>
      </el-select>
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" icon="el-icon-plus" @click="handleAdd">新增人员</el-button>
    </div>

    <!-- 人员列表表格 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="ID" width="80">
        <template slot-scope="scope">{{ scope.row.id }}</template>
      </el-table-column>
      <el-table-column align="center" label="姓名">
        <template slot-scope="scope">{{ scope.row.name }}</template>
      </el-table-column>
      <el-table-column align="center" label="性别" width="80">
        <template slot-scope="scope">
          <el-tag :type="scope.row.gender === '男' ? '' : 'danger'" size="small">{{ scope.row.gender }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="地区" width="100">
        <template slot-scope="scope">
          <el-tag type="info" size="small">{{ scope.row.region }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="联系电话">
        <template slot-scope="scope">{{ scope.row.phone }}</template>
      </el-table-column>
      <el-table-column align="center" label="职业">
        <template slot-scope="scope">{{ scope.row.occupation }}</template>
      </el-table-column>
      <el-table-column align="center" label="所属组织">
        <template slot-scope="scope">{{ scope.row.organization }}</template>
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
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="600px" :close-on-click-modal="false">
      <el-form ref="personnelForm" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名"></el-input>
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="地区" prop="region">
          <el-select v-model="form.region" placeholder="请选择地区" style="width: 100%">
            <el-option label="香港" value="香港"></el-option>
            <el-option label="澳门" value="澳门"></el-option>
            <el-option label="台湾" value="台湾"></el-option>
            <el-option label="华侨" value="华侨"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话"></el-input>
        </el-form-item>
        <el-form-item label="职业" prop="occupation">
          <el-input v-model="form.occupation" placeholder="请输入职业"></el-input>
        </el-form-item>
        <el-form-item label="所属组织" prop="organization">
          <el-input v-model="form.organization" placeholder="请输入所属组织"></el-input>
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
import { getPersonnelList, createPersonnel, updatePersonnel, deletePersonnel } from '@/api/personnel'
import Pagination from '@/components/Pagination'

export default {
  name: 'PersonnelList',
  components: { Pagination },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: false,
      listQuery: { page: 1, limit: 10, name: '', region: '' },
      dialogVisible: false,
      dialogTitle: '新增人员',
      submitLoading: false,
      isEdit: false,
      editId: null,
      form: {
        name: '',
        gender: '男',
        region: '',
        phone: '',
        occupation: '',
        organization: ''
      },
      formRules: {
        name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
        region: [{ required: true, message: '请选择地区', trigger: 'change' }],
        phone: [
          { required: true, message: '请输入联系电话', trigger: 'blur' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    // 获取人员列表
    getList() {
      this.listLoading = true
      getPersonnelList(this.listQuery).then(response => {
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
      this.dialogTitle = '新增人员'
      this.form = { name: '', gender: '男', region: '', phone: '', occupation: '', organization: '' }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.personnelForm && this.$refs.personnelForm.clearValidate()
      })
    },
    // 打开编辑弹窗
    handleEdit(row) {
      this.isEdit = true
      this.editId = row.id
      this.dialogTitle = '编辑人员'
      this.form = {
        name: row.name,
        gender: row.gender,
        region: row.region,
        phone: row.phone,
        occupation: row.occupation,
        organization: row.organization
      }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.personnelForm && this.$refs.personnelForm.clearValidate()
      })
    },
    // 提交表单
    handleSubmit() {
      this.$refs.personnelForm.validate(valid => {
        if (!valid) return
        this.submitLoading = true
        const action = this.isEdit
          ? updatePersonnel(this.editId, this.form)
          : createPersonnel(this.form)
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
    // 删除人员
    handleDelete(id) {
      this.$confirm('确认删除该人员？此操作不可恢复。', '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        deletePersonnel(id).then(() => {
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
