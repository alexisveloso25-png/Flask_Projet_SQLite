package com.aveloso;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class TaskDAO {
    private String url = "jdbc:mysql://mysql-aveloso.alwaysdata.net/aveloso_db";
    private String user = "aveloso";
    private String pass = "Favanola250505..";

    // 1. AJOUTER UNE TÂCHE
    public void addTask(String title, String desc, String date) throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
        try (Connection con = DriverManager.getConnection(url, user, pass)) {
            String sql = "INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)";
            PreparedStatement ps = con.prepareStatement(sql);
            ps.setString(1, title);
            ps.setString(2, desc);
            ps.setString(3, date);
            ps.executeUpdate();
        }
    }

    // 2. RÉCUPÉRER TOUTES LES TÂCHES (Pour l'affichage)
    public List<Task> getAllTasks() throws Exception {
        List<Task> tasks = new ArrayList<>();
        Class.forName("com.mysql.cj.jdbc.Driver");
        try (Connection con = DriverManager.getConnection(url, user, pass)) {
            String sql = "SELECT * FROM tasks ORDER BY due_date ASC";
            Statement st = con.createStatement();
            ResultSet rs = st.executeQuery(sql);

            while (rs.next()) {
                Task task = new Task();
                task.setId(rs.getInt("id"));
                task.setTitle(rs.getString("title"));
                task.setDescription(rs.getString("description"));
                task.setDueDate(rs.getString("due_date"));
                task.setCompleted(rs.getBoolean("is_completed"));
                tasks.add(task);
            }
        }
        return tasks;
    }

    // 3. SUPPRIMER UNE TÂCHE
    public void deleteTask(int id) throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
        try (Connection con = DriverManager.getConnection(url, user, pass)) {
            String sql = "DELETE FROM tasks WHERE id = ?";
            PreparedStatement ps = con.prepareStatement(sql);
            ps.setInt(1, id);
            ps.executeUpdate();
        }
    }
}
